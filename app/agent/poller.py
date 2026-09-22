"""Worker: poll eventos do hub e atualiza status local das mensagens."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.db import repos

logger = logging.getLogger("whatsmeta.poller")

_STATE = {"since": 0, "stop": False, "loaded": False}
_THREAD: Optional[threading.Thread] = None


def _map_status(raw: str) -> str:
    s = (raw or "").lower()
    mapping = {
        "sent": "SENT",
        "delivered": "DELIVERED",
        "read": "READ",
        "failed": "FAILED",
        "deleted": "FAILED",
    }
    return mapping.get(s, s.upper() if s else "UNKNOWN")


def _apply_payload(payload: Any) -> int:
    """Extrai statuses de webhook WhatsApp e atualiza whatsapp_message."""
    updated = 0
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            return 0
    if not isinstance(payload, dict):
        return 0

    entries = payload.get("entry") or []
    if not isinstance(entries, list):
        entries = [{"changes": [{"value": payload}]}]

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict):
                continue
            value = change.get("value") or {}
            if not isinstance(value, dict):
                continue
            for st in value.get("statuses") or []:
                if not isinstance(st, dict):
                    continue
                mid = st.get("id")
                status = _map_status(str(st.get("status") or ""))
                err_code = None
                err_msg = None
                errors = st.get("errors") or []
                if errors and isinstance(errors, list) and isinstance(errors[0], dict):
                    err_code = str(errors[0].get("code") or "") or None
                    err_msg = (
                        str(errors[0].get("title") or errors[0].get("message") or "")
                        or None
                    )
                if mid and status:
                    n = repos.update_message_status_by_meta_id(
                        str(mid),
                        status,
                        error_code=err_code,
                        error_message=err_msg,
                    )
                    updated += n
    return updated


def _ensure_since_loaded() -> None:
    if _STATE["loaded"]:
        return
    settings = get_settings()
    try:
        _STATE["since"] = repos.poll_state_get(settings.installation_id)
        logger.info("Poller since_id carregado=%s", _STATE["since"])
    except Exception:
        logger.exception("Poller: falha ao carregar since_id (tabela 003?)")
        _STATE["since"] = 0
    _STATE["loaded"] = True


def _persist_since() -> None:
    settings = get_settings()
    try:
        repos.poll_state_set(settings.installation_id, int(_STATE["since"]))
    except Exception:
        logger.debug("Poller: nao persistiu since_id", exc_info=True)


def poll_once() -> int:
    settings = get_settings()
    if not settings.hub_base_url or not settings.hub_pull_secret:
        logger.debug("Poller: HUB_BASE_URL/HUB_PULL_SECRET ausentes — skip")
        return 0

    _ensure_since_loaded()

    cfg = repos.get_config(settings.installation_id)
    waba_id = (cfg or {}).get("waba_id")
    if not waba_id:
        logger.debug("Poller: waba_id ausente na config — skip")
        return 0

    url = settings.hub_base_url.rstrip("/") + "/v1/hub/events"
    params: dict[str, Any] = {
        "since": _STATE["since"],
        "limit": 100,
        "waba_id": waba_id,
    }
    headers = {"X-PH-Hub-Secret": settings.hub_pull_secret}

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=params, headers=headers)
    if resp.status_code >= 400:
        logger.warning("Poller hub HTTP %s: %s", resp.status_code, resp.text[:300])
        return 0

    data = resp.json()
    events = data.get("events") or []
    total = 0
    for ev in events:
        payload = ev.get("payload_json")
        total += _apply_payload(payload)
        eid = int(ev.get("id") or 0)
        if eid > _STATE["since"]:
            _STATE["since"] = eid

    if data.get("next_since") and int(data["next_since"]) > _STATE["since"]:
        _STATE["since"] = int(data["next_since"])

    if events:
        _persist_since()

    if total:
        logger.info("Poller atualizou %s mensagem(ns)", total)
    return total


def _loop() -> None:
    settings = get_settings()
    interval = max(5, int(settings.poll_interval_seconds or 10))
    logger.info("Poller iniciado (intervalo=%ss)", interval)
    while not _STATE["stop"]:
        try:
            poll_once()
        except Exception:
            logger.exception("Poller erro")
        time.sleep(interval)


def start_poller() -> None:
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        return
    _STATE["stop"] = False
    _STATE["loaded"] = False
    _THREAD = threading.Thread(target=_loop, name="hub-poller", daemon=True)
    _THREAD.start()


def stop_poller() -> None:
    _STATE["stop"] = True
