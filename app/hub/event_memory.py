# -*- coding: utf-8 -*-
"""Fallback em memoria para eventos de webhook do hub.

Usado quando o Dev Database do App Platform nao permite CREATE TABLE
(permission denied for schema public / sem doadmin).
Single-worker: ok na v1. Perde dados no redeploy.
"""

from __future__ import annotations

import itertools
import threading
from datetime import datetime, timezone
from typing import Any, Optional

_lock = threading.Lock()
_seq = itertools.count(1)
_events: list[dict[str, Any]] = []
_MAX = 5000


def memory_insert_event(
    waba_id: Optional[str],
    field_name: Optional[str],
    payload: Any,
) -> int:
    with _lock:
        eid = next(_seq)
        _events.append(
            {
                "id": eid,
                "waba_id": waba_id,
                "field_name": field_name,
                "payload_json": payload,
                "received_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        if len(_events) > _MAX:
            del _events[: len(_events) - _MAX]
        return eid


def memory_list_events(
    *,
    waba_id: Optional[str] = None,
    since_id: int = 0,
    limit: int = 100,
) -> list[dict]:
    with _lock:
        rows = [e for e in _events if e["id"] > since_id]
        if waba_id:
            rows = [e for e in rows if str(e.get("waba_id") or "") == waba_id]
        return [dict(e) for e in rows[:limit]]


def memory_count() -> int:
    with _lock:
        return len(_events)
