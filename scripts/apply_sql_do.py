# -*- coding: utf-8 -*-
"""Aplica SQL no DATABASE_URL (forca GRANT CREATE no public se necessario)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2


def main() -> int:
    url = os.environ.get("DATABASE_URL") or ""
    if not url:
        print("ERRO: DATABASE_URL ausente")
        return 1
    root = Path(__file__).resolve().parents[1] / "sql"
    files = [
        root / "001_whatsapp_ph.sql",
        root / "002_whatsapp_pairing.sql",
        root / "003_whatsapp_poll_state.sql",
    ]
    conn = psycopg2.connect(url)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            try:
                cur.execute("GRANT USAGE, CREATE ON SCHEMA public TO CURRENT_USER")
                print("OK grant CREATE on public")
            except Exception as exc:
                print("WARN grant:", exc)
            cur.execute(
                "SELECT has_schema_privilege(current_user, 'public', 'CREATE')"
            )
            print("has CREATE:", cur.fetchone()[0])
            for f in files:
                if not f.is_file():
                    print("SKIP", f.name)
                    continue
                cur.execute(f.read_text(encoding="utf-8"))
                print("OK", f.name)
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' ORDER BY 1"
            )
            print("tables:", [r[0] for r in cur.fetchall()])
    finally:
        conn.close()
    print("Schema aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
