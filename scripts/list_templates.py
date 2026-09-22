"""Lista templates APPROVED da WABA (API oficial Meta)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings
from app.crypto import decrypt_token
from app.db import repos
from app.graph import list_message_templates


def main() -> int:
    s = get_settings()
    cfg = repos.get_config(s.installation_id)
    if not cfg or not cfg.get("access_token_enc") or not cfg.get("waba_id"):
        print("ERRO: rode scripts/seed_dev_config.py")
        return 1
    rows = list_message_templates(
        waba_id=str(cfg["waba_id"]),
        access_token=decrypt_token(cfg["access_token_enc"]),
        status="APPROVED",
    )
    print(f"WABA {cfg['waba_id']} — {len(rows)} template(s) APPROVED")
    for t in rows:
        print(
            f"- name={t.get('name')}  lang={t.get('language')}  "
            f"cat={t.get('category')}  id={t.get('id')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
