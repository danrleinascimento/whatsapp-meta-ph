"""Conexao da conta WhatsApp pelo GEPH (Embedded Signup no hub, resgate automatico aqui).

O agente gera o pair_code e o GEPH abre {HUB}/onboarding?installation_id=...&pair_code=...
O hub guarda o token com esse codigo; o poller resgata com HUB_PULL_SECRET + installation_id.
So este agente e o navegador do escritorio conhecem o codigo.

Cada clique em Conectar gera um codigo novo e os anteriores continuam valendo ate expirar:
o escritorio pode concluir o cadastro em qualquer aba aberta. Na coexistencia a sincronizacao
do app WhatsApp Business so pode ser pedida uma vez, entao um cadastro concluido nao pode se
perder. Por isso os codigos pendentes ficam tambem em arquivo (reinicio do servico). O token
resgatado fica so em memoria ate ser gravado cifrado no banco.
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.caminhos import install_dir
from app.config import get_settings
from app.crypto import encrypt_token
from app.db import repos

logger = logging.getLogger("whatsmeta.agent.onboarding")

# Mesmo formato aceito pelo hub (app/hub/routes.py).
INSTALLATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
PAIR_CODE_RE = re.compile(r"[A-Za-z0-9_-]{20,64}")
PENDING_TTL_SECONDS = 3600
MAX_PENDING = 10
PENDING_FILE_NAME = "onboarding_pendente.json"

_LOCK = threading.Lock()
# pair_code -> {"expires": epoch, "data": blob resgatado do hub ainda nao gravado}
_PENDING: dict[str, dict[str, Any]] = {}
_LOADED = {"done": False}
_LAST: dict[str, Any] = {"state": "IDLE", "message": None, "at": None}


class ClaimError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _set_last(state: str, message: Optional[str] = None) -> None:
    _LAST.update(state=state, message=message, at=datetime.now().isoformat(timespec="seconds"))


def _pending_file() -> Path:
    return install_dir() / PENDING_FILE_NAME


def _persist_locked() -> None:
    """Grava so codigo e validade (o token nunca vai para o arquivo)."""
    path = _pending_file()
    items = {code: int(item["expires"]) for code, item in _PENDING.items()}
    try:
        if not items:
            if path.exists():
                path.unlink()
            return
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(items), encoding="utf-8")
        os.replace(tmp, path)
    except OSError as exc:
        logger.warning("Nao foi possivel gravar %s: %s", path, exc)


def _load_locked() -> None:
    if _LOADED["done"]:
        return
    _LOADED["done"] = True
    path = _pending_file()
    if not path.exists():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Arquivo %s ilegivel (%s): ignorado", path, exc)
        return
    now = time.time()
    if isinstance(raw, dict):
        for code, expires in raw.items():
            if (
                isinstance(code, str)
                and PAIR_CODE_RE.fullmatch(code)
                and isinstance(expires, (int, float))
                and expires > now
            ):
                _PENDING[code] = {"expires": float(expires), "data": None}
    if _PENDING:
        _set_last("WAITING")
        logger.info("Cadastro WhatsApp: %s codigo(s) pendente(s) recuperado(s)", len(_PENDING))
    _persist_locked()


def start() -> dict[str, Any]:
    """Novo codigo de vinculacao e URL da pagina de cadastro do hub (anteriores continuam validos)."""
    settings = get_settings()
    if not settings.hub_base_url or not settings.hub_pull_secret:
        raise RuntimeError("HUB_BASE_URL/HUB_PULL_SECRET ausentes na configuracao do WHATSPH")
    if not INSTALLATION_ID_RE.fullmatch(settings.installation_id or ""):
        raise RuntimeError("INSTALLATION_ID invalido na configuracao do WHATSPH")
    code = secrets.token_urlsafe(24)
    with _LOCK:
        _load_locked()
        now = time.time()
        for old in [c for c, item in _PENDING.items() if item["expires"] <= now and item["data"] is None]:
            del _PENDING[old]
        while len(_PENDING) >= MAX_PENDING:
            oldest = min(
                (c for c, item in _PENDING.items() if item["data"] is None),
                key=lambda c: _PENDING[c]["expires"],
                default=None,
            )
            if oldest is None:
                break
            del _PENDING[oldest]
        _PENDING[code] = {"expires": now + PENDING_TTL_SECONDS, "data": None}
        _persist_locked()
        _set_last("WAITING")
    query = urlencode({"installation_id": settings.installation_id, "pair_code": code})
    logger.info("Cadastro WhatsApp iniciado (aguardando resgate no hub)")
    return {
        "onboarding_url": settings.hub_base_url.rstrip("/") + "/onboarding?" + query,
        "expires_in": PENDING_TTL_SECONDS,
    }


def status() -> dict[str, Any]:
    with _LOCK:
        _load_locked()
        return {**_LAST, "pending": len(_PENDING)}


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
    result = _save(_fetch_blob(pair_code))
    _drop_pending(pair_code, "CONNECTED")
    return result


def _drop_pending(code: str, state: str, message: Optional[str] = None) -> None:
    with _LOCK:
        if _PENDING.pop(code, None) is not None:
            _persist_locked()
        if state == "CONNECTED" or not _PENDING:
            _set_last(state, message)


def _claim_one(code: str, expires: float, data: Optional[dict[str, Any]]) -> bool:
    if data is None:
        if time.time() > expires:
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
            if code in _PENDING:
                _PENDING[code]["data"] = data
    try:
        _save(data)
    except Exception:
        # O hub ja apagou o blob: mantem os dados em memoria e tenta gravar na proxima volta.
        logger.exception("Falha ao gravar a conexao WhatsApp no banco local")
        return False
    _drop_pending(code, "CONNECTED")
    return True


def claim_pending_once() -> bool:
    """Chamado pelo poller. True quando conectou nesta chamada."""
    with _LOCK:
        _load_locked()
        items = sorted(
            ((code, item["expires"], item["data"]) for code, item in _PENDING.items()),
            key=lambda x: x[1],
        )
    connected = False
    for code, expires, data in items:
        if _claim_one(code, expires, data):
            connected = True
    return connected
