"""Auth API key (agente) e ticket do painel."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

from fastapi import Header, HTTPException

from app.config import get_settings


def require_api_key(x_ph_api_key: Optional[str] = Header(None, alias="X-PH-Api-Key")) -> str:
    expected = get_settings().ph_api_key
    if not expected:
        raise HTTPException(status_code=500, detail="PH_API_KEY nao configurado")
    if not x_ph_api_key or not hmac.compare_digest(x_ph_api_key, expected):
        raise HTTPException(status_code=401, detail="API key invalida")
    return x_ph_api_key


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_panel_ticket(usuario_geph: str, ttl_seconds: int = 300) -> str:
    secret = get_settings().panel_ticket_secret
    if not secret:
        raise RuntimeError("PANEL_TICKET_SECRET nao configurado")
    exp = int(time.time()) + ttl_seconds
    payload = f"{usuario_geph}|{exp}"
    sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}|{sig}"


def verify_panel_ticket(ticket: str) -> str:
    secret = get_settings().panel_ticket_secret
    if not secret:
        raise HTTPException(status_code=500, detail="PANEL_TICKET_SECRET nao configurado")
    parts = (ticket or "").split("|")
    if len(parts) != 3:
        raise HTTPException(status_code=403, detail="Ticket invalido")
    usuario, exp_s, sig = parts
    payload = f"{usuario}|{exp_s}"
    expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=403, detail="Ticket invalido")
    try:
        exp = int(exp_s)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Ticket invalido") from exc
    if time.time() > exp:
        raise HTTPException(status_code=403, detail="Ticket expirado")
    if not usuario:
        raise HTTPException(status_code=403, detail="Ticket sem usuario")
    return usuario
