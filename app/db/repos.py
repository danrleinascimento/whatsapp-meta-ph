"""Repositorios Postgres locais / hub."""

from __future__ import annotations

import json
from typing import Any, Optional

from app.db import execute, fetch_all, fetch_one


def get_config(installation_id: str) -> Optional[dict]:
    return fetch_one(
        "SELECT * FROM whatsapp_config WHERE installation_id = %s",
        (installation_id,),
    )


def upsert_config(
    installation_id: str,
    *,
    status: str,
    waba_id: Optional[str] = None,
    phone_number_id: Optional[str] = None,
    display_phone: Optional[str] = None,
    graph_api_version: Optional[str] = None,
    access_token_enc: Optional[str] = None,
    last_error: Optional[str] = None,
) -> None:
    existing = get_config(installation_id)
    if existing:
        execute(
            """
            UPDATE whatsapp_config SET
              status = %s,
              waba_id = COALESCE(%s, waba_id),
              phone_number_id = COALESCE(%s, phone_number_id),
              display_phone = COALESCE(%s, display_phone),
              graph_api_version = COALESCE(%s, graph_api_version),
              access_token_enc = COALESCE(%s, access_token_enc),
              last_error = %s,
              connected_at = CASE WHEN %s = 'CONNECTED' THEN CURRENT_TIMESTAMP ELSE connected_at END,
              updated_at = CURRENT_TIMESTAMP
            WHERE installation_id = %s
            """,
            (
                status,
                waba_id,
                phone_number_id,
                display_phone,
                graph_api_version,
                access_token_enc,
                last_error,
                status,
                installation_id,
            ),
        )
    else:
        execute(
            """
            INSERT INTO whatsapp_config (
              installation_id, status, waba_id, phone_number_id, display_phone,
              graph_api_version, access_token_enc, last_error, connected_at
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,
              CASE WHEN %s = 'CONNECTED' THEN CURRENT_TIMESTAMP ELSE NULL END)
            """,
            (
                installation_id,
                status,
                waba_id,
                phone_number_id,
                display_phone,
                graph_api_version or "v25.0",
                access_token_enc,
                last_error,
                status,
            ),
        )


def insert_message(
    *,
    installation_id: str,
    msg_type: str,
    to_wa_id: str,
    status: str,
    direction: str = "OUT",
    template_name: Optional[str] = None,
    caption: Optional[str] = None,
    local_file_path: Optional[str] = None,
    media_id: Optional[str] = None,
    meta_message_id: Optional[str] = None,
    http_status: Optional[int] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    sistema_origem: Optional[str] = None,
    usuario_geph: Optional[str] = None,
    hostname: Optional[str] = None,
) -> int:
    row = fetch_one(
        """
        INSERT INTO whatsapp_message (
          installation_id, direction, msg_type, to_wa_id, template_name, caption,
          local_file_path, media_id, meta_message_id, status, http_status,
          error_code, error_message, sistema_origem, usuario_geph, hostname
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
        """,
        (
            installation_id,
            direction,
            msg_type,
            to_wa_id,
            template_name,
            caption,
            local_file_path,
            media_id,
            meta_message_id,
            status,
            http_status,
            error_code,
            error_message,
            sistema_origem,
            usuario_geph,
            hostname,
        ),
    )
    return int(row["id"]) if row else 0


def list_messages(installation_id: str, limit: int = 100) -> list[dict]:
    return fetch_all(
        """
        SELECT id, direction, msg_type, to_wa_id, template_name, caption,
               local_file_path, media_id, meta_message_id, status,
               error_code, error_message, sistema_origem, usuario_geph,
               hostname, created_at, updated_at
        FROM whatsapp_message
        WHERE installation_id = %s
        ORDER BY id DESC
        LIMIT %s
        """,
        (installation_id, limit),
    )


def update_message_status_by_meta_id(
    meta_message_id: str,
    status: str,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> int:
    return execute(
        """
        UPDATE whatsapp_message SET
          status = %s,
          error_code = COALESCE(%s, error_code),
          error_message = COALESCE(%s, error_message),
          updated_at = CURRENT_TIMESTAMP
        WHERE meta_message_id = %s
        """,
        (status, error_code, error_message, meta_message_id),
    )


# --- Hub event store (mesmas tabelas no DO ou whatsapp_webhook_event) ---

_SCHEMA_OK: Optional[bool] = None


def _hub_schema_available() -> bool:
    global _SCHEMA_OK
    if _SCHEMA_OK is not None:
        return _SCHEMA_OK
    try:
        from app.db.migrate import schema_ok

        _SCHEMA_OK = schema_ok()
    except Exception:
        _SCHEMA_OK = False
    return _SCHEMA_OK


def invalidate_schema_cache() -> None:
    global _SCHEMA_OK
    _SCHEMA_OK = None


def hub_insert_event(waba_id: Optional[str], field_name: Optional[str], payload: Any) -> None:
    if _hub_schema_available():
        try:
            execute(
                """
                INSERT INTO whatsapp_webhook_event (waba_id, field_name, payload_json)
                VALUES (%s, %s, %s)
                """,
                (waba_id, field_name, json.dumps(payload, ensure_ascii=False)),
            )
            return
        except Exception:
            invalidate_schema_cache()
    from app.hub.event_memory import memory_insert_event

    memory_insert_event(waba_id, field_name, payload)


def hub_list_events(
    *,
    waba_id: Optional[str] = None,
    since_id: int = 0,
    limit: int = 100,
) -> list[dict]:
    if _hub_schema_available():
        try:
            if waba_id:
                return fetch_all(
                    """
                    SELECT id, waba_id, field_name, payload_json, received_at
                    FROM whatsapp_webhook_event
                    WHERE id > %s AND waba_id = %s
                    ORDER BY id ASC
                    LIMIT %s
                    """,
                    (since_id, waba_id, limit),
                )
            return fetch_all(
                """
                SELECT id, waba_id, field_name, payload_json, received_at
                FROM whatsapp_webhook_event
                WHERE id > %s
                ORDER BY id ASC
                LIMIT %s
                """,
                (since_id, limit),
            )
        except Exception:
            invalidate_schema_cache()
    from app.hub.event_memory import memory_list_events

    return memory_list_events(waba_id=waba_id, since_id=since_id, limit=limit)


# --- Pairing blobs (hub) ---


def pairing_store_db(
    *,
    pair_code: str,
    installation_id: str,
    waba_id: Optional[str],
    phone_number_id: Optional[str],
    access_token: str,
    display_phone: Optional[str],
    graph_api_version: str,
    expires_at,
) -> None:
    execute(
        """
        INSERT INTO whatsapp_pairing_blob (
          pair_code, installation_id, waba_id, phone_number_id, display_phone,
          graph_api_version, access_token, claimed, expires_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,FALSE,%s)
        """,
        (
            pair_code,
            installation_id,
            waba_id,
            phone_number_id,
            display_phone,
            graph_api_version,
            access_token,
            expires_at,
        ),
    )


def pairing_claim_db(pair_code: str, installation_id: str) -> Optional[dict]:
    row = fetch_one(
        """
        SELECT pair_code, installation_id, waba_id, phone_number_id, display_phone,
               graph_api_version, access_token, claimed, expires_at
        FROM whatsapp_pairing_blob
        WHERE pair_code = %s
        """,
        (pair_code,),
    )
    if not row:
        return None
    if row.get("claimed"):
        return {"__error__": "claimed"}
    if str(row.get("installation_id") or "") != installation_id:
        return {"__error__": "installation"}
    # expires_at pode ser datetime
    exp = row.get("expires_at")
    try:
        import datetime as _dt

        now = _dt.datetime.utcnow()
        if hasattr(exp, "tzinfo") and exp.tzinfo is not None:
            now = _dt.datetime.now(exp.tzinfo)
        if exp is not None and now > exp:
            execute("DELETE FROM whatsapp_pairing_blob WHERE pair_code = %s", (pair_code,))
            return {"__error__": "expired"}
    except Exception:
        pass
    execute(
        """
        UPDATE whatsapp_pairing_blob SET claimed = TRUE
        WHERE pair_code = %s
        """,
        (pair_code,),
    )
    execute("DELETE FROM whatsapp_pairing_blob WHERE pair_code = %s", (pair_code,))
    return {
        "installation_id": row.get("installation_id"),
        "waba_id": row.get("waba_id"),
        "phone_number_id": row.get("phone_number_id"),
        "display_phone": row.get("display_phone"),
        "graph_api_version": row.get("graph_api_version"),
        "access_token": row.get("access_token"),
    }


# --- Poller cursor (agente) ---


def poll_state_get(installation_id: str) -> int:
    row = fetch_one(
        "SELECT since_id FROM whatsapp_poll_state WHERE installation_id = %s",
        (installation_id,),
    )
    if not row:
        return 0
    return int(row.get("since_id") or 0)


def poll_state_set(installation_id: str, since_id: int) -> None:
    existing = fetch_one(
        "SELECT installation_id FROM whatsapp_poll_state WHERE installation_id = %s",
        (installation_id,),
    )
    if existing:
        execute(
            """
            UPDATE whatsapp_poll_state
            SET since_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE installation_id = %s
            """,
            (since_id, installation_id),
        )
    else:
        execute(
            """
            INSERT INTO whatsapp_poll_state (installation_id, since_id)
            VALUES (%s, %s)
            """,
            (installation_id, since_id),
        )
