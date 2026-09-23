# -*- coding: utf-8 -*-
"""Aplica sql/001..003. Prefer DATABASE_URL do ambiente; senao Settings/.env."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psycopg2


def main() -> int:
    # Garante .env do cwd (pasta WHATSPH)
    try:
        from dotenv import load_dotenv

        load_dotenv(Path.cwd() / ".env", override=False)
    except Exception:
        pass

    url = os.environ.get("DATABASE_URL") or ""
    if not url:
        from app.config import clear_settings_cache, get_settings

        clear_settings_cache()
        url = get_settings().database_url
    if not url:
        print("ERRO: DATABASE_URL ausente no ambiente/.env")
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
            for f in files:
                if not f.is_file():
                    print("SKIP", f.name)
                    continue
                cur.execute(f.read_text(encoding="utf-8"))
                print("OK", f.name)
    finally:
        conn.close()
    print("Schema aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
