"""Webhook Meta WhatsApp — verificacao GET + eventos POST.

Documentacao oficial:
https://developers.facebook.com/docs/graph-api/webhooks/getting-started
https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse

from app.config import get_settings
from app.db import repos

logger = logging.getLogger("whatsmeta.webhook")

router = APIRouter(tags=["webhook"])


def _validar_assinatura(raw_body: bytes, signature_header: Optional[str], app_secret: str) -> bool:
    """Valida X-Hub-Signature-256: sha256=<hex> com HMAC-SHA256(app_secret, body)."""
    if not app_secret:
        return False
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = signature_header.split("=", 1)[1].strip()
    digest = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, expected)


# Coexistencia: historico de conversas e contatos do app WhatsApp Business. Nenhuma parte
# do sistema usa esse conteudo e o hub so repassa eventos (politica de privacidade).
_CAMPOS_NAO_PERSISTIDOS = frozenset({"history", "smb_app_state_sync"})


def _separar_campos_nao_persistidos(payload: Any) -> tuple[Any, list[tuple[Any, dict[str, Any]]]]:
    """Retorna (payload sem esses campos ou None se nada sobrar, [(waba_id, change removido)])."""
    if not isinstance(payload, dict) or not isinstance(payload.get("entry"), list):
        return payload, []
    removidos: list[tuple[Any, dict[str, Any]]] = []
    entries: list[Any] = []
    for entry in payload["entry"]:
        changes = entry.get("changes") if isinstance(entry, dict) else None
        if not isinstance(changes, list):
            entries.append(entry)
            continue
        mantidos = []
        for change in changes:
            if isinstance(change, dict) and change.get("field") in _CAMPOS_NAO_PERSISTIDOS:
                removidos.append((entry.get("id"), change))
            else:
                mantidos.append(change)
        if mantidos:
            entries.append({**entry, "changes": mantidos})
    if not removidos:
        return payload, []
    return ({**payload, "entry": entries} if entries else None), removidos


def _resumo_sync(change: dict[str, Any]) -> str:
    """Progresso da sincronizacao (sem conteudo das conversas) para o log."""
    value = change.get("value") if isinstance(change.get("value"), dict) else {}
    if change.get("field") == "smb_app_state_sync":
        itens = value.get("state_sync")
        return f"contatos={len(itens) if isinstance(itens, list) else 0}"
    partes = []
    for item in value.get("history") or []:
        if not isinstance(item, dict):
            continue
        for err in item.get("errors") or []:
            if isinstance(err, dict):
                partes.append(f"erro={err.get('code')}")
        meta = item.get("metadata")
        if isinstance(meta, dict):
            partes.append(f"fase={meta.get('phase')} progresso={meta.get('progress')}")
    return " ".join(partes) or "sem metadata"


def _extract_waba_and_field(payload: Any) -> tuple[Optional[str], Optional[str]]:
    if not isinstance(payload, dict):
        return None, None
    entries = payload.get("entry")
    if not isinstance(entries, list) or not entries:
        return None, None
    entry0 = entries[0] if isinstance(entries[0], dict) else {}
    waba_id = entry0.get("id")
    field_name = None
    changes = entry0.get("changes")
    if isinstance(changes, list) and changes and isinstance(changes[0], dict):
        field_name = changes[0].get("field")
    return (str(waba_id) if waba_id else None), (str(field_name) if field_name else None)


@router.get("/webhook/whatsapp")
async def verificar_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
) -> Response:
    """Handshake de verificacao da Meta (App Dashboard)."""
    settings = get_settings()
    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="hub.mode invalido")

    if not settings.meta_webhook_verify_token:
        raise HTTPException(
            status_code=500,
            detail="META_WEBHOOK_VERIFY_TOKEN nao configurado no servidor",
        )

    if hub_verify_token != settings.meta_webhook_verify_token:
        logger.warning("Verify token rejeitado")
        raise HTTPException(status_code=403, detail="Verify token invalido")

    if hub_challenge is None or hub_challenge == "":
        raise HTTPException(status_code=400, detail="hub.challenge ausente")

    return PlainTextResponse(content=str(hub_challenge), status_code=200)


@router.post("/webhook/whatsapp")
async def receber_evento_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
) -> dict[str, str]:
    """Recebe Event Notifications da Meta. Persiste e responde 200 rapido."""
    settings = get_settings()
    raw = await request.body()

    if not settings.meta_app_secret:
        logger.error("META_APP_SECRET nao configurado — rejeitando webhook")
        raise HTTPException(status_code=500, detail="META_APP_SECRET nao configurado")

    if not _validar_assinatura(raw, x_hub_signature_256, settings.meta_app_secret):
        logger.error("Assinatura X-Hub-Signature-256 invalida")
        raise HTTPException(status_code=403, detail="Assinatura invalida")

    try:
        payload: Any = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        logger.exception("Payload webhook nao-JSON")
        raise HTTPException(status_code=400, detail="JSON invalido") from None

    obj = payload.get("object") if isinstance(payload, dict) else None
    entries = payload.get("entry") if isinstance(payload, dict) else None
    n = len(entries) if isinstance(entries, list) else 0
    logger.info("Webhook recebido object=%s entries=%s bytes=%s", obj, n, len(raw))

    payload, removidos = _separar_campos_nao_persistidos(payload)
    for waba_removido, change in removidos:
        logger.info(
            "Webhook %s waba=%s nao persistido: %s",
            change.get("field"),
            waba_removido,
            _resumo_sync(change),
        )
    if payload is None:
        return {"status": "ok"}

    waba_id, field_name = _extract_waba_and_field(payload)
    try:
        if settings.database_url:
            repos.hub_insert_event(waba_id, field_name, payload)
        else:
            logger.warning("DATABASE_URL ausente — evento nao persistido")
    except Exception:
        logger.exception("Falha ao persistir webhook (ainda responde 200)")

    return {"status": "ok"}
