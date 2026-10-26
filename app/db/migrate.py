# -*- coding: utf-8 -*-
"""Aplica sql/*.sql no DATABASE_URL (hub/agente). Best-effort no startup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn

from app.caminhos import resource_dir
from app.config import get_settings
from app.db.connection import abrir_conexao

logger = logging.getLogger("whatsmeta.migrate")

_SQL_DIR = resource_dir() / "sql"

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
        conn = abrir_conexao()
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


# Chave do pg_advisory_lock: duas preparacoes ao mesmo tempo nao criam o banco duas vezes.
_LOCK_CRIAR_BANCO = 72840131


def garantir_banco() -> bool:
    """Cria o banco do DATABASE_URL (UTF8) se ainda nao existir. True se criou agora."""
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL ausente no .env")
    nome = parse_dsn(url).get("dbname")
    if not nome:
        raise RuntimeError("DATABASE_URL sem o nome do banco")
    conn = None
    for base in ("postgres", "template1"):
        try:
            conn = abrir_conexao(dbname=base, connect_timeout=5)
            break
        except psycopg2.OperationalError:
            if base == "template1":
                raise
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s)", (_LOCK_CRIAR_BANCO,))
            try:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (nome,))
                if cur.fetchone() is not None:
                    return False
                cur.execute(
                    sql.SQL("CREATE DATABASE {} ENCODING 'UTF8' TEMPLATE template0").format(sql.Identifier(nome))
                )
                logger.info("Banco %s criado", nome)
                return True
            finally:
                cur.execute("SELECT pg_advisory_unlock(%s)", (_LOCK_CRIAR_BANCO,))
    finally:
        conn.close()


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
    conn = abrir_conexao()
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
