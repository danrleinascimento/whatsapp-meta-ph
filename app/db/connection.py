"""Conexao Postgres (psycopg2) — compativel com PG 9.5."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Optional

import psycopg2
import psycopg2.extras

from app.config import get_settings


def db_ok() -> bool:
    url = get_settings().database_url
    if not url:
        return False
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:
        return False


@contextmanager
def connect() -> Iterator[Any]:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL nao configurado")
    conn = psycopg2.connect(settings.database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_one(sql: str, params: Optional[tuple] = None) -> Optional[dict]:
    with connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def fetch_all(sql: str, params: Optional[tuple] = None) -> list[dict]:
    with connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def execute(sql: str, params: Optional[tuple] = None) -> int:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount
