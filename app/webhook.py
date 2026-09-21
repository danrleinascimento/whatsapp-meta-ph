"""Webhook Meta WhatsApp — verificacao GET + eventos POST.

Documentacao oficial:
https://developers.facebook.com/docs/graph-api/webhooks/getting-started
https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import PlainTextResponse

from app.config import get_settings

logger = logging.getLogger("whatsmeta.webhook")

router = APIRouter(tags=["webhook"])


def _validar_assinatura(raw_body: bytes, signature_header: Optional[str], app_secret: str) -> bool:
    """Valida X-Hub-Signature-256: sha256=<hex> com HMAC-SHA256(app_secret, body)."""
    if not app_secret:
        # Em desenvolvimento sem secret: nao rejeita, mas registra aviso.
        logger.warning("META_APP_SECRET vazio — assinatura do webhook NAO validada")
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = signature_header.split("=", 1)[1].strip()
    digest = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, expected)


@router.get("/webhook/whatsapp")
async def verificar_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
) -> Response:
    """Handshake de verificacao da Meta (App Dashboard).

    Deve devolver o hub.challenge em texto puro (nao JSON) com HTTP 200.
    """
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

    # Resposta EXATA: corpo = challenge, content-type text/plain
    return PlainTextResponse(content=str(hub_challenge), status_code=200)


@router.post("/webhook/whatsapp")
async def receber_evento_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
) -> dict[str, str]:
    """Recebe Event Notifications da Meta.

    Responde 200 imediatamente. Persistencia/fila entram em fases seguintes.
    """
    import json

    settings = get_settings()
    raw = await request.body()

    if not _validar_assinatura(raw, x_hub_signature_256, settings.meta_app_secret):
        logger.error("Assinatura X-Hub-Signature-256 invalida")
        raise HTTPException(status_code=403, detail="Assinatura invalida")

    try:
        payload: Any = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        logger.exception("Payload webhook nao-JSON")
        raise HTTPException(status_code=400, detail="JSON invalido") from None

    # Log minimo (sem dados sensiveis de usuario em excesso na v1)
    obj = payload.get("object") if isinstance(payload, dict) else None
    entries = payload.get("entry") if isinstance(payload, dict) else None
    n = len(entries) if isinstance(entries, list) else 0
    logger.info("Webhook recebido object=%s entries=%s bytes=%s", obj, n, len(raw))

    # TODO fase seguinte: gravar em Postgres, idempotencia, encaminhar ao agente local
    return {"status": "ok"}
