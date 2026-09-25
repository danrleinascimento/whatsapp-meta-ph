"""Servico de envio WhatsApp no agente local."""

from __future__ import annotations

import logging
import socket
import time
from typing import Any, Optional

from app.agent.path_guard import resolve_allowed_pdf
from app.agent.phone import normalize_wa_id
from app.config import get_settings
from app.crypto import decrypt_token
from app.db import repos
from app.graph import (
    GraphError,
    build_document_payload,
    build_template_payload,
    build_text_payload,
    extract_message_id,
    resolve_template,
    send_message,
    upload_pdf,
)

logger = logging.getLogger("whatsmeta.agent.send")

# Controle simples de pair-rate por destinatario (mesmo processo)
_last_send_by_to: dict[str, float] = {}


def _wait_pair_rate(to_wa_id: str) -> None:
    settings = get_settings()
    min_s = float(settings.pair_rate_min_seconds or 6.0)
    now = time.monotonic()
    last = _last_send_by_to.get(to_wa_id, 0.0)
    wait = min_s - (now - last)
    if wait > 0:
        time.sleep(wait)


def _mark_sent(to_wa_id: str) -> None:
    _last_send_by_to[to_wa_id] = time.monotonic()


def get_connected_config() -> dict:
    settings = get_settings()
    cfg = repos.get_config(settings.installation_id)
    if not cfg:
        raise RuntimeError("whatsapp_config ausente - rode scripts/seed_dev_config.py")
    if cfg.get("status") != "CONNECTED":
        raise RuntimeError(f"WhatsApp nao CONECTADO (status={cfg.get('status')})")
    if not cfg.get("phone_number_id"):
        raise RuntimeError("phone_number_id ausente na config")
    if not cfg.get("access_token_enc"):
        raise RuntimeError("access_token_enc ausente na config")
    return cfg


def _access_token(cfg: dict) -> str:
    return decrypt_token(cfg["access_token_enc"])


def _extra_roots(diretorio_principal: Optional[str], diretorio_secundario: Optional[str]) -> list[str]:
    settings = get_settings()
    roots: list[str] = []
    for v in (
        diretorio_principal,
        diretorio_secundario,
        settings.diretorio_principal,
        settings.diretorio_secundario,
    ):
        if v:
            roots.append(v)
    return roots


def send_template(
    *,
    to: str,
    template_name: str,
    language_code: Optional[str] = None,
    components: Optional[list[dict[str, Any]]] = None,
    sistema_origem: Optional[str] = None,
    usuario_geph: Optional[str] = None,
) -> dict[str, Any]:
    """Envia template apos resolver name+language APPROVED na WABA (doc Meta)."""
    settings = get_settings()
    cfg = get_connected_config()
    to_wa = normalize_wa_id(to)
    token = _access_token(cfg)

    # Valida/resolve contra GET /{WABA}/message_templates (evita 132001)
    resolved = resolve_template(
        waba_id=str(cfg["waba_id"]),
        access_token=token,
        template_name=template_name,
        language_code=language_code,
    )
    payload = build_template_payload(
        to_wa,
        template_name=resolved["name"],
        language_code=resolved["language"],
        components=components,
    )
    result = _dispatch(
        cfg=cfg,
        installation_id=settings.installation_id,
        msg_type="template",
        to_wa_id=to_wa,
        payload=payload,
        template_name=resolved["name"],
        sistema_origem=sistema_origem,
        usuario_geph=usuario_geph,
        access_token=token,
    )
    result["template_resolved"] = {
        "name": resolved["name"],
        "language": resolved["language"],
        "category": resolved.get("category"),
        "resolved_from": resolved.get("resolved_from"),
    }
    return result


def send_text(
    *,
    to: str,
    body: str,
    sistema_origem: Optional[str] = None,
    usuario_geph: Optional[str] = None,
) -> dict[str, Any]:
    settings = get_settings()
    cfg = get_connected_config()
    to_wa = normalize_wa_id(to)
    payload = build_text_payload(to_wa, body)
    return _dispatch(
        cfg=cfg,
        installation_id=settings.installation_id,
        msg_type="text",
        to_wa_id=to_wa,
        payload=payload,
        caption=body,
        sistema_origem=sistema_origem,
        usuario_geph=usuario_geph,
    )


def send_document(
    *,
    to: str,
    file_path: str,
    caption: Optional[str] = None,
    diretorio_principal: Optional[str] = None,
    diretorio_secundario: Optional[str] = None,
    sistema_origem: Optional[str] = None,
    usuario_geph: Optional[str] = None,
    force_session: bool = False,
    body_name: Optional[str] = None,
    body_detail: Optional[str] = None,
    envio_tipo: str = "boleto",
) -> dict[str, Any]:
    """Envia PDF.

    Regra oficial Meta (Cloud API / service messages):
    - Dentro da janela 24h: mensagem livre tipo ``document`` OK.
    - Fora da janela 24h: obrigatorio template aprovado (utility) com header DOCUMENT.

    envio_tipo:
    - ``boleto``: template ph_boleto_pdf (grupo de boletos).
    - ``relatorio``: template ph_relatorio_pdf (Preview avulso / SenWA).
    """
    settings = get_settings()
    to_wa = normalize_wa_id(to)
    pdf = resolve_allowed_pdf(
        file_path,
        extra_roots=_extra_roots(diretorio_principal, diretorio_secundario),
    )
    cfg = get_connected_config()
    token = _access_token(cfg)
    try:
        media_id = upload_pdf(
            phone_number_id=cfg["phone_number_id"],
            access_token=token,
            file_path=pdf,
        )
    except GraphError as exc:
        mid = repos.insert_message(
            installation_id=settings.installation_id,
            msg_type="document",
            to_wa_id=to_wa,
            status="FAILED",
            caption=caption,
            local_file_path=str(pdf),
            http_status=exc.http_status,
            error_code=exc.error_code,
            error_message=str(exc),
            sistema_origem=sistema_origem,
            usuario_geph=usuario_geph,
            hostname=socket.gethostname(),
        )
        return {
            "ok": False,
            "message_id": mid,
            "error": str(exc),
            "error_code": exc.error_code,
            "http_status": exc.http_status,
        }

    tipo, tpl_name, tpl_lang = _resolve_envio_tipo(envio_tipo)
    tpl = None if force_session else _approved_document_template(cfg, token, tpl_name, tpl_lang)
    if tpl:
        components: list[dict[str, Any]] = [
            {
                "type": "header",
                "parameters": [
                    {
                        "type": "document",
                        "document": {"id": media_id, "filename": pdf.name},
                    }
                ],
            }
        ]
        nparams = _template_body_param_count(tpl)
        if nparams >= 1:
            if tipo == "relatorio":
                texts = [_template_text_param(body_name or "relatorio")]
            else:
                texts = [_template_text_param(body_name or "")]
                if nparams >= 2:
                    texts.append(
                        _template_text_param(body_detail or _caption_as_body_detail(caption))
                    )
            while len(texts) < nparams:
                texts.append("-")
            components.append(
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": t} for t in texts[:nparams]],
                }
            )
        payload = build_template_payload(
            to_wa,
            template_name=tpl["name"],
            language_code=tpl["language"],
            components=components,
        )
        result = _dispatch(
            cfg=cfg,
            installation_id=settings.installation_id,
            msg_type="template",
            to_wa_id=to_wa,
            payload=payload,
            template_name=tpl["name"],
            caption=caption,
            local_file_path=str(pdf),
            media_id=media_id,
            sistema_origem=sistema_origem,
            usuario_geph=usuario_geph,
            access_token=token,
        )
        result["delivery_mode"] = "template"
        result["envio_tipo"] = tipo
        result["template_resolved"] = {
            "name": tpl["name"],
            "language": tpl["language"],
            "status": tpl.get("status"),
        }
        return result

    payload = build_document_payload(
        to_wa,
        media_id=media_id,
        caption=caption,
        filename=pdf.name,
    )
    result = _dispatch(
        cfg=cfg,
        installation_id=settings.installation_id,
        msg_type="document",
        to_wa_id=to_wa,
        payload=payload,
        caption=caption,
        local_file_path=str(pdf),
        media_id=media_id,
        sistema_origem=sistema_origem,
        usuario_geph=usuario_geph,
        access_token=token,
    )
    result["delivery_mode"] = "session"
    result["envio_tipo"] = tipo
    result["warning"] = (
        "PDF enviado como mensagem de sessao (livre). "
        "Pela regra oficial da Meta, fora da janela de 24h apos a ultima mensagem "
        "do cliente a API pode aceitar (ACCEPTED) e o celular nao receber. "
        f"Para envio sem mensagem recente do cliente, aguarde o modelo {tpl_name} "
        "aprovado na Meta."
    )
    return result


def _resolve_envio_tipo(envio_tipo: str) -> tuple[str, str, str]:
    settings = get_settings()
    tipo = (envio_tipo or "boleto").strip().lower()
    if tipo == "relatorio":
        name = (settings.whatsapp_relatorio_template_name or "ph_relatorio_pdf").strip()
        lang = (settings.whatsapp_relatorio_template_lang or "pt_BR").strip()
        return "relatorio", name, lang
    name = (settings.whatsapp_boleto_template_name or "ph_boleto_pdf").strip()
    lang = (settings.whatsapp_boleto_template_lang or "pt_BR").strip()
    return "boleto", name, lang


def _template_text_param(raw: str) -> str:
    """Parametros de body do template nao podem ser vazios (Meta)."""
    s = (raw or "").replace("\r", " ").replace("\n", " ").strip()
    if not s:
        return "-"
    return s[:1024]


def _caption_as_body_detail(caption: Optional[str]) -> str:
    if not caption:
        return "-"
    # Compacta caption multilinha do GEPH em um detalhe curto
    line = " ".join(part.strip() for part in caption.replace("\r\n", "\n").split("\n") if part.strip())
    return line[:1024] if line else "-"


def _template_body_param_count(tpl: dict[str, Any]) -> int:
    import re

    for comp in tpl.get("components") or []:
        if not isinstance(comp, dict):
            continue
        if str(comp.get("type") or "").upper() != "BODY":
            continue
        text = str(comp.get("text") or "")
        return len(re.findall(r"\{\{\d+\}\}", text))
    return 0


def _approved_document_template(
    cfg: dict,
    token: str,
    name: str,
    lang: str,
) -> Optional[dict[str, Any]]:
    """Retorna template APPROVED com header DOCUMENT, ou None."""
    from app.graph.templates import list_message_templates

    name = (name or "").strip()
    if not name:
        return None
    lang = (lang or "").strip() or None
    waba = str(cfg.get("waba_id") or "")
    if not waba:
        return None
    try:
        rows = list_message_templates(
            waba_id=waba,
            access_token=token,
            name=name,
            language=lang,
            status="APPROVED",
        )
    except Exception:
        logger.exception("Falha ao listar template %s", name)
        return None
    for row in rows:
        if str(row.get("name") or "") != name:
            continue
        if lang and str(row.get("language") or "") != lang:
            continue
        if str(row.get("status") or "").upper() != "APPROVED":
            continue
        has_doc_header = False
        for comp in row.get("components") or []:
            if not isinstance(comp, dict):
                continue
            if str(comp.get("type") or "").upper() != "HEADER":
                continue
            if str(comp.get("format") or "").upper() == "DOCUMENT":
                has_doc_header = True
                break
        if has_doc_header:
            return row
    return None


def send_batch(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Envia sequencialmente com delay e pair-rate por destinatario."""
    settings = get_settings()
    results: list[dict[str, Any]] = []
    for item in items:
        kind = (item.get("type") or item.get("msg_type") or "").lower()
        common = {
            "sistema_origem": item.get("sistema_origem"),
            "usuario_geph": item.get("usuario_geph"),
        }
        try:
            if kind == "template":
                r = send_template(
                    to=item["to"],
                    template_name=item["template_name"],
                    language_code=item.get("language_code") or None,
                    components=item.get("components"),
                    **common,
                )
            elif kind == "document":
                r = send_document(
                    to=item["to"],
                    file_path=item["file_path"],
                    caption=item.get("caption"),
                    diretorio_principal=item.get("diretorio_principal"),
                    diretorio_secundario=item.get("diretorio_secundario"),
                    **common,
                )
            elif kind == "text":
                r = send_text(to=item["to"], body=item["body"], **common)
            else:
                r = {"ok": False, "error": f"tipo invalido: {kind}"}
        except Exception as exc:
            logger.exception("Falha no item de batch")
            r = {"ok": False, "error": str(exc)}
        results.append(r)
        time.sleep(float(settings.batch_delay_seconds or 0.05))
    ok_n = sum(1 for r in results if r.get("ok"))
    return {"ok": ok_n == len(results), "total": len(results), "accepted": ok_n, "results": results}


def _dispatch(
    *,
    cfg: dict,
    installation_id: str,
    msg_type: str,
    to_wa_id: str,
    payload: dict[str, Any],
    template_name: Optional[str] = None,
    caption: Optional[str] = None,
    local_file_path: Optional[str] = None,
    media_id: Optional[str] = None,
    sistema_origem: Optional[str] = None,
    usuario_geph: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict[str, Any]:
    token = access_token or _access_token(cfg)
    _wait_pair_rate(to_wa_id)
    try:
        resp = send_message(
            phone_number_id=cfg["phone_number_id"],
            access_token=token,
            payload=payload,
        )
        meta_id = extract_message_id(resp)
        _mark_sent(to_wa_id)
        mid = repos.insert_message(
            installation_id=installation_id,
            msg_type=msg_type,
            to_wa_id=to_wa_id,
            status="ACCEPTED",
            template_name=template_name,
            caption=caption,
            local_file_path=local_file_path,
            media_id=media_id,
            meta_message_id=meta_id,
            http_status=200,
            sistema_origem=sistema_origem,
            usuario_geph=usuario_geph,
            hostname=socket.gethostname(),
        )
        return {
            "ok": True,
            "message_id": mid,
            "meta_message_id": meta_id,
            "status": "ACCEPTED",
            "graph": resp,
        }
    except GraphError as exc:
        mid = repos.insert_message(
            installation_id=installation_id,
            msg_type=msg_type,
            to_wa_id=to_wa_id,
            status="FAILED",
            template_name=template_name,
            caption=caption,
            local_file_path=local_file_path,
            media_id=media_id,
            http_status=exc.http_status,
            error_code=exc.error_code,
            error_message=str(exc),
            sistema_origem=sistema_origem,
            usuario_geph=usuario_geph,
            hostname=socket.gethostname(),
        )
        return {
            "ok": False,
            "message_id": mid,
            "error": str(exc),
            "error_code": exc.error_code,
            "http_status": exc.http_status,
        }
