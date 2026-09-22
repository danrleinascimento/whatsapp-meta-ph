"""
Seed da config de desenvolvimento (WABA/Phone Number PH Softwares).

Uso (na pasta do projeto, com .venv ativo):
  python scripts/seed_dev_config.py

Requer no .env:
  DATABASE_URL, TOKEN_ENCRYPTION_KEY, INSTALLATION_ID (opcional)
  META_ACCESS_TOKEN, META_PHONE_NUMBER_ID, META_WABA_ID
  META_DISPLAY_PHONE (opcional)
"""

from __future__ import annotations

import os
import sys

# Garante import do pacote app/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import clear_settings_cache, get_settings
from app.crypto import encrypt_token
from app.db import repos
from app.agent.auth import hash_api_key


def main() -> int:
    clear_settings_cache()
    s = get_settings()
    if not s.database_url:
        print("ERRO: DATABASE_URL ausente")
        return 1
    if not s.token_encryption_key:
        print("ERRO: TOKEN_ENCRYPTION_KEY ausente")
        return 1
    if not s.meta_access_token:
        print("ERRO: META_ACCESS_TOKEN ausente no .env (token System User / permanente de teste)")
        return 1
    if not s.meta_phone_number_id:
        print("ERRO: META_PHONE_NUMBER_ID ausente")
        return 1
    if not s.meta_waba_id:
        print("ERRO: META_WABA_ID ausente")
        return 1

    enc = encrypt_token(s.meta_access_token)
    repos.upsert_config(
        s.installation_id,
        status="CONNECTED",
        waba_id=s.meta_waba_id,
        phone_number_id=s.meta_phone_number_id,
        display_phone=s.meta_display_phone or None,
        graph_api_version=s.graph_api_version,
        access_token_enc=enc,
        last_error=None,
    )

    if s.ph_api_key:
        from app.db import execute, fetch_one

        existing = fetch_one(
            "SELECT id FROM whatsapp_local_auth WHERE installation_id = %s",
            (s.installation_id,),
        )
        h = hash_api_key(s.ph_api_key)
        if existing:
            execute(
                "UPDATE whatsapp_local_auth SET api_key_hash=%s, updated_at=CURRENT_TIMESTAMP WHERE installation_id=%s",
                (h, s.installation_id),
            )
        else:
            execute(
                "INSERT INTO whatsapp_local_auth (installation_id, api_key_hash) VALUES (%s,%s)",
                (s.installation_id, h),
            )

    cfg = repos.get_config(s.installation_id)
    print("OK — config gravada")
    print(f"  installation_id = {s.installation_id}")
    print(f"  status          = {cfg.get('status') if cfg else '?'}")
    print(f"  waba_id         = {cfg.get('waba_id') if cfg else '?'}")
    print(f"  phone_number_id = {cfg.get('phone_number_id') if cfg else '?'}")
    print(f"  display_phone   = {cfg.get('display_phone') if cfg else '?'}")
    print("  access_token    = *** (cifrado)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
