# -*- coding: utf-8 -*-
"""Aplica sql/*.sql no DATABASE_URL (hub/agente). Best-effort no startup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import psycopg2

from app.config import get_settings

logger = logging.getLogger("whatsmeta.migrate")

_SQL_DIR = Path(__file__).resolve().parents[2] / "sql"

# Hub precisa destas; agente local usa 001+003 (+002 opcional)
HUB_SQL_FILES = (
    "001_whatsapp_ph.sql",
    "002_whatsapp_pairing.sql",
)
AGENT_SQL_FILES = (
    "001_whatsapp_ph.sql",
    "002_whatsapp_pairing.sql",
    "003_whatsapp_poll_state.sql",
)


def schema_ok() -> bool:
    """True se a tabela critica do webhook existe."""
    url = get_settings().database_url
    if not url:
        return False
    try:
        conn = psycopg2.connect(url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'whatsapp_webhook_event'
                    """
                )
                return cur.fetchone() is not None
        finally:
            conn.close()
    except Exception:
        return False


def apply_sql_files(file_names: tuple[str, ...] | list[str]) -> dict[str, Any]:
    """
    Aplica arquivos SQL. Retorna dict com ok, applied, errors.
    Tenta GRANT CREATE no public (pode falhar no Dev DB do App Platform).
    """
    settings = get_settings()
    if not settings.database_url:
        return {"ok": False, "applied": [], "errors": ["DATABASE_URL ausente"], "schema_ok": False}

    applied: list[str] = []
    errors: list[str] = []
    conn = psycopg2.connect(settings.database_url)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            try:
                cur.execute("GRANT USAGE, CREATE ON SCHEMA public TO CURRENT_USER")
            except Exception as exc:
                logger.warning("GRANT CREATE no public falhou (esperado em Dev DB): %s", exc)

            for name in file_names:
                path = _SQL_DIR / name
                if not path.is_file():
                    errors.append(f"{name}: arquivo ausente")
                    continue
                try:
                    cur.execute(path.read_text(encoding="utf-8"))
                    applied.append(name)
                    logger.info("SQL OK %s", name)
                except Exception as exc:
                    msg = f"{name}: {exc}"
                    errors.append(msg)
                    logger.error("SQL FALHOU %s", msg)
    finally:
        conn.close()

    ok = schema_ok()
    return {
        "ok": ok,
        "applied": applied,
        "errors": errors,
        "schema_ok": ok,
    }


def migrate_for_role(role: str) -> dict[str, Any]:
    names = HUB_SQL_FILES if role == "hub" else AGENT_SQL_FILES
    if schema_ok():
        logger.info("Schema ja presente — migrate skip")
        return {"ok": True, "applied": [], "errors": [], "schema_ok": True, "skipped": True}
    return apply_sql_files(names)
