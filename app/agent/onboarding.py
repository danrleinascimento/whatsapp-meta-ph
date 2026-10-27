"""Conexao da conta WhatsApp pelo GEPH (Embedded Signup no hub, resgate automatico aqui).

O agente gera o pair_code e o GEPH abre {HUB}/onboarding?installation_id=...&pair_code=...
O hub guarda o token com esse codigo; o poller resgata com HUB_PULL_SECRET + installation_id.
So este agente e o navegador do escritorio conhecem o codigo.
"""

from __future__ import annotations

import logging
import re
import secrets
import threading
import time
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.crypto import encrypt_token
from app.db import repos

logger = logging.getLogger("whatsmeta.agent.onboarding")

# Mesmo formato aceito pelo hub (app/hub/routes.py).
INSTALLATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
PENDING_TTL_SECONDS = 3600

_LOCK = threading.Lock()
_PENDING: dict[str, Any] = {}
_LAST: dict[str, Any] = {"state": "IDLE", "message": None, "at": None}


class ClaimError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _set_last(state: str, message: Optional[str] = None) -> None:
    _LAST.update(state=state, message=message, at=datetime.now().isoformat(timespec="seconds"))


def start() -> dict[str, Any]:
    """Novo codigo de vinculacao (substitui o anterior) e URL da pagina de cadastro do hub."""
    settings = get_settings()
    if not settings.hub_base_url or not settings.hub_pull_secret:
        raise RuntimeError("HUB_BASE_URL/HUB_PULL_SECRET ausentes na configuracao do WHATSPH")
    if not INSTALLATION_ID_RE.fullmatch(settings.installation_id or ""):
        raise RuntimeError("INSTALLATION_ID invalido na configuracao do WHATSPH")
    code = secrets.token_urlsafe(24)
    with _LOCK:
        _PENDING.clear()
        _PENDING.update(code=code, expires=time.monotonic() + PENDING_TTL_SECONDS)
        _set_last("WAITING")
    query = urlencode({"installation_id": settings.installation_id, "pair_code": code})
    logger.info("Cadastro WhatsApp iniciado (aguardando resgate no hub)")
    return {
        "onboarding_url": settings.hub_base_url.rstrip("/") + "/onboarding?" + query,
        "expires_in": PENDING_TTL_SECONDS,
    }


def status() -> dict[str, Any]:
    with _LOCK:
        return dict(_LAST)


def _fetch_blob(pair_code: str) -> dict[str, Any]:
    """POST /v1/hub/pairing/claim. O hub apaga o blob ao entregar (uso unico)."""
    settings = get_settings()
    if not settings.hub_base_url or not settings.hub_pull_secret:
        raise ClaimError(500, "HUB_BASE_URL/HUB_PULL_SECRET ausentes")
    url = settings.hub_base_url.rstrip("/") + "/v1/hub/pairing/claim"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            url,
            params={"pair_code": pair_code, "installation_id": settings.installation_id},
            headers={"X-PH-Hub-Secret": settings.hub_pull_secret},
        )
    if resp.status_code >= 400:
        raise ClaimError(resp.status_code, resp.text[:500])
    data = resp.json()
    if not isinstance(data, dict) or not data.get("access_token"):
        raise ClaimError(502, "Hub nao retornou access_token")
    if not data.get("waba_id") or not data.get("phone_number_id"):
        raise ClaimError(502, "Hub nao retornou waba_id/phone_number_id")
    return data


def _save(data: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    repos.upsert_config(
        settings.installation_id,
        status="CONNECTED",
        waba_id=data.get("waba_id"),
        phone_number_id=data.get("phone_number_id"),
        display_phone=data.get("display_phone"),
        graph_api_version=data.get("graph_api_version") or settings.graph_api_version,
        access_token_enc=encrypt_token(data["access_token"]),
        last_error=None,
    )
    from app.agent.template_setup import request_check

    request_check()
    logger.info(
        "WhatsApp conectado waba=%s phone=%s", data.get("waba_id"), data.get("phone_number_id")
    )
    return {
        "ok": True,
        "status": "CONNECTED",
        "waba_id": data.get("waba_id"),
        "phone_number_id": data.get("phone_number_id"),
        "display_phone": data.get("display_phone"),
    }


def claim(pair_code: str) -> dict[str, Any]:
    """Resgate manual (pair_code mostrado na pagina). ClaimError com o status HTTP do hub."""
    return _save(_fetch_blob(pair_code))


def _drop_pending(code: str, state: str, message: Optional[str] = None) -> None:
    with _LOCK:
        if _PENDING.get("code") == code:
            _PENDING.clear()
            _set_last(state, message)


def claim_pending_once() -> bool:
    """Chamado pelo poller. True quando conectou nesta chamada."""
    with _LOCK:
        code = _PENDING.get("code")
        expires = float(_PENDING.get("expires") or 0)
        data = _PENDING.get("data")
    if not code:
        return False
    if data is None:
        if time.monotonic() > expires:
            _drop_pending(code, "EXPIRED", "Cadastro nao concluido em 1 hora. Abra Conectar conta WhatsApp de novo.")
            return False
        try:
            data = _fetch_blob(code)
        except ClaimError as exc:
            if exc.status_code == 404 or exc.status_code >= 500:
                return False
            logger.error("Resgate do cadastro recusado pelo hub (HTTP %s): %s", exc.status_code, exc.detail)
            _drop_pending(code, "ERROR", f"Hub recusou o resgate (HTTP {exc.status_code}).")
            return False
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Resgate do cadastro: hub inacessivel (%s)", exc.__class__.__name__)
            return False
        with _LOCK:
            if _PENDING.get("code") == code:
                _PENDING["data"] = data
    try:
        _save(data)
    except Exception:
        # O hub ja apagou o blob: mantem os dados em memoria e tenta gravar na proxima volta.
        logger.exception("Falha ao gravar a conexao WhatsApp no banco local")
        return False
    _drop_pending(code, "CONNECTED")
    return True
