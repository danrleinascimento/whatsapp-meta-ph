# -*- coding: utf-8 -*-
"""Cria template utility ph_relatorio_pdf (header DOCUMENT) na WABA."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.pop("DATABASE_URL", None)
load_dotenv(ROOT / ".env", override=True)

from app.config import clear_settings_cache, get_settings
from app.crypto import decrypt_token
from app.db import repos
from app.graph.client import _base_url
from create_boleto_template import _sample_pdf, resumable_upload_handle

TEMPLATE_NAME = "ph_relatorio_pdf"
LANGUAGE = "pt_BR"
# Variavel no meio do texto (regra Meta: nao no inicio nem no fim).
BODY = "Relatorio gerado no Sistema PH: {{1}}. O PDF segue em anexo."


def main() -> int:
    clear_settings_cache()
    s = get_settings()
    cfg = repos.get_config(s.installation_id)
    if not cfg:
        print("ERRO: config ausente")
        return 1
    token = decrypt_token(cfg["access_token_enc"])
    waba = str(cfg["waba_id"])
    app_id = s.meta_app_id
    if not app_id:
        print("ERRO: META_APP_ID ausente")
        return 1

    with httpx.Client(timeout=60.0) as client:
        listed = client.get(
            f"{_base_url()}/{waba}/message_templates",
            headers={"Authorization": f"Bearer {token}"},
            params={"name": TEMPLATE_NAME, "fields": "name,language,status,id"},
        )
        listed.raise_for_status()
        for row in listed.json().get("data") or []:
            if row.get("name") == TEMPLATE_NAME and row.get("language") == LANGUAGE:
                print("JA_EXISTE", row.get("status"), row.get("id"))
                return 0

    pdf = _sample_pdf()
    handle = resumable_upload_handle(app_id=app_id, token=token, file_path=pdf)
    print("handle_ok", len(handle))
    payload = {
        "name": TEMPLATE_NAME,
        "language": LANGUAGE,
        "category": "UTILITY",
        "components": [
            {
                "type": "HEADER",
                "format": "DOCUMENT",
                "example": {"header_handle": [handle]},
            },
            {
                "type": "BODY",
                "text": BODY,
                "example": {"body_text": [["Balancete"]]},
            },
            {"type": "FOOTER", "text": "PH Softwares"},
        ],
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{_base_url()}/{waba}/message_templates",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
        )
        print("CREATE", resp.status_code, resp.text[:800])
        return 0 if resp.status_code < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main())
