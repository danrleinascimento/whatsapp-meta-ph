# -*- coding: utf-8 -*-
"""Cria template utility ph_boleto_pdf (header DOCUMENT) na WABA — API oficial Meta.

Fontes:
- https://developers.facebook.com/docs/graph-api/guides/upload/
- https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/
- https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/components
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.pop("DATABASE_URL", None)
load_dotenv(ROOT / ".env", override=True)

from app.config import clear_settings_cache, get_settings
from app.crypto import decrypt_token
from app.db import repos
from app.graph.client import _base_url


TEMPLATE_NAME = "ph_boleto_pdf"
LANGUAGE = "pt_BR"


def _sample_pdf() -> Path:
    p = Path(r"C:\PHSFTW") / "_sample_boleto_template.pdf"
    if not p.parent.exists():
        p = Path(r"D:\PHSFTW") / "_sample_boleto_template.pdf"
    p.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
        b"4 0 obj<< /Length 48 >>stream\n"
        b"BT /F1 14 Tf 20 100 Td (Boleto PH Softwares) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000262 00000 n \n0000000360 00000 n \n"
        b"trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n437\n%%EOF\n"
    )
    return p


def resumable_upload_handle(*, app_id: str, token: str, file_path: Path) -> str:
    data = file_path.read_bytes()
    with httpx.Client(timeout=120.0) as client:
        r1 = client.post(
            f"{_base_url()}/{app_id}/uploads",
            params={
                "file_name": file_path.name,
                "file_length": str(len(data)),
                "file_type": "application/pdf",
                "access_token": token,
            },
        )
        r1.raise_for_status()
        session_id = r1.json().get("id")
        if not session_id:
            raise RuntimeError(f"upload session sem id: {r1.text}")
        # id vem como "upload:..." 
        upload_path = session_id if str(session_id).startswith("upload:") else f"upload:{session_id}"
        r2 = client.post(
            f"{_base_url()}/{upload_path}",
            headers={
                "Authorization": f"OAuth {token}",
                "file_offset": "0",
                "Content-Type": "application/octet-stream",
            },
            content=data,
        )
        r2.raise_for_status()
        handle = r2.json().get("h")
        if not handle:
            raise RuntimeError(f"upload sem handle: {r2.text}")
        return str(handle)


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
        print("ERRO: META_APP_ID ausente no .env")
        return 1

    # Já existe?
    with httpx.Client(timeout=60.0) as client:
        listed = client.get(
            f"{_base_url()}/{waba}/message_templates",
            headers={"Authorization": f"Bearer {token}"},
            params={"name": TEMPLATE_NAME, "fields": "name,language,status,category,components"},
        )
        listed.raise_for_status()
        for row in listed.json().get("data") or []:
            if row.get("name") == TEMPLATE_NAME and row.get("language") == LANGUAGE:
                print("JA_EXISTE", row.get("status"), row.get("id"))
                print(row)
                return 0

    pdf = _sample_pdf()
    print("PDF sample", pdf, pdf.stat().st_size)
    handle = resumable_upload_handle(app_id=app_id, token=token, file_path=pdf)
    print("handle_ok len", len(handle))

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
                "text": (
                    "Olá{{1}}! Segue o PDF do seu boleto"
                    "{{2}}. Qualquer dúvida, responda esta mensagem."
                ),
                "example": {
                    "body_text": [["", " (competência 09/2026)"]]
                },
            },
            {
                "type": "FOOTER",
                "text": "PH Softwares",
            },
        ],
    }
    # Fix body: Meta requires {{1}} {{2}} with spaces typically "Olá {{1}}!"
    payload["components"][1]["text"] = (
        "Ola {{1}}! Segue o PDF do seu boleto{{2}}. "
        "Qualquer duvida, responda esta mensagem."
    )
    payload["components"][1]["example"] = {
        "body_text": [["cliente", " (competencia 09/2026)"]]
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{_base_url()}/{waba}/message_templates",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        print("CREATE", resp.status_code, resp.text[:800])
        if resp.status_code >= 400:
            return 1
        print("OK — aguarde status APPROVED no WhatsApp Manager / listagem")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
