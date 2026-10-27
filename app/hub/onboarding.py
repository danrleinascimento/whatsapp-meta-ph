"""Passos server-to-server do hub depois do Embedded Signup (Tech Provider + coexistencia).

Documentacao oficial Meta:
https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-customers-as-a-tech-provider
https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users
https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/manage-accounts

Coexistencia (numero do app WhatsApp Business): o evento da sessao traz so o waba_id,
o numero ja esta registrado (nao chamar /register) e a sincronizacao de contatos e de
historico (smb_app_data) tem de ser pedida em ate 24 h, uma unica vez cada.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("whatsmeta.hub.onboarding")

COEXISTENCE_EVENT = "FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING"
_DIGITS = re.compile(r"\d{1,32}")
_TIMEOUT = 20.0


class OnboardingError(Exception):
    """Impede concluir a conexao. A mensagem vai para a pagina do escritorio."""


@dataclass
class OnboardingResult:
    access_token: str
    waba_id: str
    phone_number_id: str
    display_phone: Optional[str]
    verified_name: Optional[str]
    coexistence: bool
    warnings: list[str] = field(default_factory=list)


def only_digits(value: Optional[str]) -> Optional[str]:
    text = (value or "").strip()
    return text if _DIGITS.fullmatch(text) else None


def _url(path: str) -> str:
    return f"https://graph.facebook.com/{get_settings().graph_api_version}/{path.lstrip('/')}"


def _error_text(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except ValueError:
        return f"HTTP {resp.status_code}"
    err = data.get("error") if isinstance(data, dict) else None
    if not isinstance(err, dict):
        return f"HTTP {resp.status_code}"
    text = str(err.get("error_user_msg") or err.get("message") or f"HTTP {resp.status_code}")
    if err.get("code") is not None:
        text += f" (codigo {err.get('code')})"
    return text


def _call(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    token: Optional[str] = None,
    params: Optional[dict[str, Any]] = None,
    json_body: Optional[dict[str, Any]] = None,
    retry: bool = False,
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Retorna (json, None) em 2xx ou (None, texto do erro). retry: repete 1x em rede/5xx."""
    headers = {"Authorization": f"Bearer {token}"} if token else None
    attempts = 2 if retry else 1
    error = "sem resposta"
    for _ in range(attempts):
        try:
            resp = client.request(method, _url(path), params=params, json=json_body, headers=headers)
        except httpx.TransportError as exc:
            error = f"falha de rede: {exc.__class__.__name__}"
            continue
        if resp.status_code < 400:
            try:
                data = resp.json()
            except ValueError:
                data = {}
            return (data if isinstance(data, dict) else {"data": data}), None
        error = _error_text(resp)
        if resp.status_code < 500:
            break
    return None, error


def _exchange_code(client: httpx.Client, code: str) -> str:
    settings = get_settings()
    try:
        resp = client.get(
            _url("oauth/access_token"),
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "code": code,
            },
        )
    except httpx.TransportError as exc:
        raise OnboardingError(
            f"Falha de rede ao falar com a Meta ({exc.__class__.__name__}). Tente o cadastro de novo."
        ) from exc
    if resp.status_code >= 400:
        detail = _error_text(resp)
        logger.error("Troca do code falhou: %s", detail)
        raise OnboardingError(
            "A Meta recusou a finalização do cadastro: " + detail
            + ". O código da Meta vale só 30 segundos; clique no botão e faça o cadastro de novo."
        )
    token: Optional[str] = None
    try:
        data = resp.json()
        if isinstance(data, dict):
            token = data.get("access_token")
    except ValueError:
        text = resp.text.strip()
        if text and not any(ch.isspace() for ch in text):
            token = text
    if not token:
        raise OnboardingError("A Meta não devolveu o acesso da conta. Faça o cadastro de novo.")
    return str(token)


def _debug_token(client: httpx.Client, token: str) -> tuple[Optional[str], Optional[int]]:
    """WABA mais recente com whatsapp_business_management e expires_at (0 = nunca expira)."""
    settings = get_settings()
    data, err = _call(
        client,
        "GET",
        "debug_token",
        params={
            "input_token": token,
            "access_token": f"{settings.meta_app_id}|{settings.meta_app_secret}",
        },
    )
    if err or not data:
        logger.warning("debug_token falhou: %s", err)
        return None, None
    info = data.get("data") if isinstance(data.get("data"), dict) else {}
    waba_id: Optional[str] = None
    for scope in info.get("granular_scopes") or []:
        if isinstance(scope, dict) and scope.get("scope") == "whatsapp_business_management":
            targets = scope.get("target_ids") or []
            if targets:
                waba_id = only_digits(str(targets[0]))
            break
    expires_at = info.get("expires_at")
    return waba_id, (int(expires_at) if isinstance(expires_at, (int, float)) else None)


def _pick_phone(
    client: httpx.Client, token: str, waba_id: str, hint: Optional[str]
) -> dict[str, Any]:
    data, err = _call(
        client,
        "GET",
        f"{waba_id}/phone_numbers",
        token=token,
        params={"fields": "id,display_phone_number,verified_name"},
        retry=True,
    )
    if err or data is None:
        raise OnboardingError("Não foi possível ler o número da conta WhatsApp na Meta: " + str(err))
    phones = [p for p in data.get("data") or [] if isinstance(p, dict) and p.get("id")]
    if hint:
        for phone in phones:
            if str(phone.get("id")) == hint:
                return phone
    if len(phones) == 1:
        return phones[0]
    if not phones:
        raise OnboardingError(
            "A conta WhatsApp conectada não tem número. Refaça o cadastro escolhendo o número "
            "do WhatsApp Business do escritório."
        )
    on_app = []
    for phone in phones:
        flags, _ = _call(client, "GET", str(phone["id"]), token=token, params={"fields": "is_on_biz_app"})
        if flags and flags.get("is_on_biz_app") is True:
            on_app.append(phone)
    if len(on_app) == 1:
        return on_app[0]
    raise OnboardingError(
        "A conta WhatsApp tem mais de um número e não foi possível saber qual usar. "
        "Fale com o suporte da PH Softwares."
    )


def _phone_platform(
    client: httpx.Client, token: str, phone_id: str
) -> tuple[Optional[bool], Optional[str]]:
    data, err = _call(
        client, "GET", phone_id, token=token, params={"fields": "is_on_biz_app,platform_type"}, retry=True
    )
    if err or data is None:
        logger.warning("is_on_biz_app/platform_type falhou phone=%s: %s", phone_id, err)
        return None, None
    on_app = data.get("is_on_biz_app")
    platform = data.get("platform_type")
    return (on_app if isinstance(on_app, bool) else None), (str(platform) if platform else None)


def run_onboarding(
    *,
    code: str,
    waba_hint: Optional[str],
    phone_hint: Optional[str],
    flow_event: Optional[str],
) -> OnboardingResult:
    settings = get_settings()
    if not settings.meta_app_id or not settings.meta_app_secret:
        raise OnboardingError("Servidor da PH Softwares sem META_APP_ID / META_APP_SECRET. Fale com o suporte.")

    with httpx.Client(timeout=_TIMEOUT) as client:
        token = _exchange_code(client, code)
        warnings: list[str] = []

        token_waba, expires_at = _debug_token(client, token)
        waba_id = waba_hint or token_waba
        if not waba_id:
            raise OnboardingError(
                "A Meta não informou qual conta WhatsApp foi conectada. Faça o cadastro de novo."
            )
        if expires_at:
            quando = datetime.fromtimestamp(expires_at, tz=timezone.utc).strftime("%d/%m/%Y")
            logger.warning("Token da WABA %s expira em %s (configuracao com expiracao)", waba_id, quando)
            warnings.append(
                f"O acesso concedido à PH Softwares expira em {quando}. Antes dessa data será "
                "preciso conectar a conta de novo."
            )

        _, err = _call(client, "POST", f"{waba_id}/subscribed_apps", token=token, retry=True)
        if err:
            logger.error("subscribed_apps falhou waba=%s: %s", waba_id, err)
            warnings.append(
                "A Meta não confirmou o aviso de entrega das mensagens (" + err + "). "
                "O envio funciona, mas a situação Entregue/Lida pode não aparecer. Avise o suporte."
            )

        phone = _pick_phone(client, token, waba_id, phone_hint)
        phone_id = str(phone["id"])
        on_app, platform = _phone_platform(client, token, phone_id)

        if on_app is True:
            coexistence = True
        elif on_app is False:
            coexistence = False
            if platform != "CLOUD_API":
                raise OnboardingError(
                    "Este número não está no app WhatsApp Business. No cadastro, escolha a opção de "
                    "conectar a conta existente do WhatsApp Business e informe o número que o "
                    "escritório já usa no app."
                )
        else:
            coexistence = flow_event == COEXISTENCE_EVENT
            if not coexistence:
                warnings.append(
                    "Não foi possível confirmar na Meta se o número está no app WhatsApp Business."
                )

        if coexistence:
            for sync_type, nome in (("smb_app_state_sync", "contatos"), ("history", "histórico")):
                data, err = _call(
                    client,
                    "POST",
                    f"{phone_id}/smb_app_data",
                    token=token,
                    json_body={"messaging_product": "whatsapp", "sync_type": sync_type},
                    retry=True,
                )
                if err:
                    logger.error("smb_app_data %s falhou phone=%s: %s", sync_type, phone_id, err)
                    warnings.append(f"A sincronização de {nome} com o WhatsApp Business falhou: {err}.")
                else:
                    logger.info(
                        "smb_app_data %s phone=%s request_id=%s",
                        sync_type,
                        phone_id,
                        (data or {}).get("request_id"),
                    )

    logger.info(
        "Onboarding OK waba=%s phone=%s coexistencia=%s platform=%s evento=%s",
        waba_id,
        phone_id,
        coexistence,
        platform,
        flow_event,
    )
    return OnboardingResult(
        access_token=token,
        waba_id=waba_id,
        phone_number_id=phone_id,
        display_phone=phone.get("display_phone_number"),
        verified_name=phone.get("verified_name"),
        coexistence=coexistence,
        warnings=warnings,
    )
