# -*- coding: utf-8 -*-
"""Aplica SQL no Postgres DO como doadmin (GRANT + 001/002/003).

Uso:
  set DATABASE_URL=postgresql://whatsapp-meta-db:...@host:25060/whatsapp-meta-db?sslmode=require
  set DOADMIN_PASSWORD=<senha do doadmin>
  python scripts/apply_sql_doadmin.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

import psycopg2


def build_doadmin_url(app_url: str, doadmin_password: str) -> str:
    p = urlparse(app_url)
    host = p.hostname or ""
    port = p.port or 25060
    path = p.path or "/whatsapp-meta-db"
    query = p.query or "sslmode=require"
    netloc = f"doadmin:{quote_plus(doadmin_password)}@{host}:{port}"
    return urlunparse((p.scheme or "postgresql", netloc, path, "", query, ""))


def main() -> int:
    app_url = os.environ.get("DATABASE_URL") or ""
    doadmin_password = os.environ.get("DOADMIN_PASSWORD") or ""
    if not app_url:
        print("ERRO: DATABASE_URL ausente")
        return 1
    if not doadmin_password:
        print("ERRO: DOADMIN_PASSWORD ausente")
        print("No DigitalOcean: Databases / Connection Details -> usuario doadmin -> senha")
        return 1

    url = build_doadmin_url(app_url, doadmin_password)
    print("Conectando como doadmin...")
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT current_user")
    print("OK user=", cur.fetchone()[0])

    cur.execute('GRANT USAGE, CREATE ON SCHEMA public TO "whatsapp-meta-db"')
    cur.execute('GRANT ALL ON SCHEMA public TO "whatsapp-meta-db"')
    cur.execute(
        'ALTER DEFAULT PRIVILEGES FOR ROLE doadmin IN SCHEMA public '
        'GRANT ALL ON TABLES TO "whatsapp-meta-db"'
    )
    print("OK GRANT CREATE para whatsapp-meta-db")

    root = Path(__file__).resolve().parents[1] / "sql"
    for name in (
        "001_whatsapp_ph.sql",
        "002_whatsapp_pairing.sql",
        "003_whatsapp_poll_state.sql",
    ):
        f = root / name
        cur.execute(f.read_text(encoding="utf-8"))
        print("OK", name)

    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' ORDER BY 1"
    )
    print("tables:", [r[0] for r in cur.fetchall()])
    cur.close()
    conn.close()
    print("Schema DO aplicado com sucesso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
