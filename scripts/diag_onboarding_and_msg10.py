# -*- coding: utf-8 -*-
"""Diagnostico: onboarding hub + mensagem id=10."""
from __future__ import annotations

import os
import re
import sys

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.pop("DATABASE_URL", None)
load_dotenv(override=True)

from app.config import clear_settings_cache, get_settings
from app.crypto import decrypt_token
from app.db import repos
from app.db.connection import fetch_one


def main() -> int:
    clear_settings_cache()
    s = get_settings()
    print("local META_APP_ID set:", bool(s.meta_app_id))
    print("local META_EMBEDDED_SIGNUP_CONFIG_ID set:", bool(s.meta_embedded_signup_config_id))

    hub = (s.hub_base_url or "https://whatsapp-meta-ph-wzewk.ondigitalocean.app").rstrip("/")
    with httpx.Client(timeout=30.0) as client:
        h = client.get(f"{hub}/health")
        print("hub health:", h.status_code, h.text[:300])
        page = client.get(f"{hub}/onboarding?installation_id=local-dev")
        print("onboarding status:", page.status_code)
        app_m = re.search(r"const APP_ID = (.*?);", page.text)
        cfg_m = re.search(r"const CONFIG_ID = (.*?);", page.text)
        print("hub APP_ID literal:", app_m.group(1) if app_m else None)
        print("hub CONFIG_ID literal:", cfg_m.group(1) if cfg_m else None)

        # msg 10 via DB local
        row = fetch_one(
            """
            SELECT id, created_at, to_wa_id, status, meta_message_id,
                   caption, local_file_path, error_code, error_message, http_status
            FROM whatsapp_messages WHERE id = 10
            """
        )
        print("msg10:", dict(row) if row else None)

        cfg = repos.get_config(s.installation_id)
        if cfg and row and row.get("meta_message_id"):
            token = decrypt_token(cfg["access_token_enc"])
            mid = row["meta_message_id"]
            # Meta nao garante GET por wamid; tenta mesmo assim
            url = f"https://graph.facebook.com/{s.graph_api_version}/{mid}"
            r = client.get(url, headers={"Authorization": f"Bearer {token}"})
            print("graph GET wamid:", r.status_code, r.text[:400])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
