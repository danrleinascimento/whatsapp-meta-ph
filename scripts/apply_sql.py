"""Aplica sql/001..003 no DATABASE_URL do .env (local ou tipado para DO)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psycopg2

from app.config import get_settings


def main() -> int:
    s = get_settings()
    if not s.database_url:
        print("ERRO: DATABASE_URL ausente")
        return 1
    root = Path(__file__).resolve().parents[1] / "sql"
    files = [
        root / "001_whatsapp_ph.sql",
        root / "002_whatsapp_pairing.sql",
        root / "003_whatsapp_poll_state.sql",
    ]
    conn = psycopg2.connect(s.database_url)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            for f in files:
                if not f.is_file():
                    print("SKIP", f.name, "(ausente)")
                    continue
                sql = f.read_text(encoding="utf-8")
                cur.execute(sql)
                print("OK", f.name)
    finally:
        conn.close()
    print("Schema aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
