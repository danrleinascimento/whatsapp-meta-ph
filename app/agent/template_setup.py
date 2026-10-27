"""Cria na WABA do escritorio os templates de documento usados pelo send_document.

Mesmo conteudo dos templates APPROVED na WABA da PH Softwares (ph_boleto_pdf / ph_relatorio_pdf).
O exemplo do header DOCUMENT exige um handle da Resumable Upload API (POST /{APP_ID}/uploads).

Fontes:
https://developers.facebook.com/docs/graph-api/guides/upload/
https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.crypto import decrypt_token
from app.db import repos
from app.graph.client import _base_url, _parse_error
from app.graph.templates import list_message_templates

logger = logging.getLogger("whatsmeta.agent.templates")

_INTERVAL_OK_SECONDS = 6 * 3600
_INTERVAL_FAIL_SECONDS = 30 * 60
_STATE = {"next": 0.0}
_LOCK = threading.Lock()

_SAMPLE_PDF = (
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


def _definitions() -> list[dict[str, Any]]:
    s = get_settings()
    return [
        {
            "name": (s.whatsapp_boleto_template_name or "ph_boleto_pdf").strip(),
            "language": (s.whatsapp_boleto_template_lang or "pt_BR").strip(),
            "body": "Ola {{1}}! Segue o PDF do seu boleto{{2}}. Qualquer duvida, responda esta mensagem.",
            "example": [["cliente", " (competencia 09/2026)"]],
        },
        {
            "name": (s.whatsapp_relatorio_template_name or "ph_relatorio_pdf").strip(),
            "language": (s.whatsapp_relatorio_template_lang or "pt_BR").strip(),
            "body": "Relatorio gerado no Sistema PH: {{1}}. O PDF segue em anexo.",
            "example": [["Balancete"]],
        },
    ]


def _upload_handle(client: httpx.Client, *, app_id: str, token: str) -> str:
    r1 = client.post(
        f"{_base_url()}/{app_id}/uploads",
        params={
            "file_name": "exemplo_ph.pdf",
            "file_length": str(len(_SAMPLE_PDF)),
            "file_type": "application/pdf",
            "access_token": token,
        },
    )
    if r1.status_code >= 400:
        raise _parse_error(r1)
    session_id = str((r1.json() or {}).get("id") or "")
    if not session_id:
        raise RuntimeError("Resumable Upload sem id de sessao")
    upload_path = session_id if session_id.startswith("upload:") else f"upload:{session_id}"
    r2 = client.post(
        f"{_base_url()}/{upload_path}",
        headers={
            "Authorization": f"OAuth {token}",
            "file_offset": "0",
            "Content-Type": "application/octet-stream",
        },
        content=_SAMPLE_PDF,
    )
    if r2.status_code >= 400:
        raise _parse_error(r2)
    handle = (r2.json() or {}).get("h")
    if not handle:
        raise RuntimeError("Resumable Upload sem handle")
    return str(handle)


def _create(client: httpx.Client, *, waba_id: str, token: str, app_id: str, tpl: dict[str, Any]) -> str:
    handle = _upload_handle(client, app_id=app_id, token=token)
    payload = {
        "name": tpl["name"],
        "language": tpl["language"],
        "category": "UTILITY",
        "components": [
            {"type": "HEADER", "format": "DOCUMENT", "example": {"header_handle": [handle]}},
            {"type": "BODY", "text": tpl["body"], "example": {"body_text": tpl["example"]}},
            {"type": "FOOTER", "text": "PH Softwares"},
        ],
    }
    resp = client.post(
        f"{_base_url()}/{waba_id}/message_templates",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    if resp.status_code >= 400:
        raise _parse_error(resp)
    return str((resp.json() or {}).get("status") or "")


def ensure_document_templates(cfg: dict[str, Any]) -> bool:
    """True quando os dois templates existem (qualquer status) ou foram criados agora."""
    app_id = get_settings().meta_app_id
    if not app_id:
        logger.warning("META_APP_ID ausente no .env do WHATSPH: templates de documento nao criados")
        return False
    waba_id = str(cfg["waba_id"])
    token = decrypt_token(cfg["access_token_enc"])
    all_ok = True
    with httpx.Client(timeout=60.0) as client:
        for tpl in _definitions():
            try:
                rows = list_message_templates(
                    waba_id=waba_id,
                    access_token=token,
                    name=tpl["name"],
                    fields="name,language,status",
                )
                existing = next(
                    (
                        r
                        for r in rows
                        if r.get("name") == tpl["name"] and r.get("language") == tpl["language"]
                    ),
                    None,
                )
                if existing:
                    st = str(existing.get("status") or "")
                    if st.upper() in ("REJECTED", "DISABLED", "PAUSED"):
                        logger.warning("Template %s na WABA %s com status %s", tpl["name"], waba_id, st)
                    continue
                st = _create(client, waba_id=waba_id, token=token, app_id=app_id, tpl=tpl)
                logger.info("Template %s criado na WABA %s (status %s)", tpl["name"], waba_id, st)
            except Exception as exc:
                all_ok = False
                logger.warning("Template %s na WABA %s: %s", tpl["name"], waba_id, exc)
    return all_ok


def request_check() -> None:
    """Pede verificacao na proxima volta do poller (logo apos conectar)."""
    with _LOCK:
        _STATE["next"] = 0.0


def maybe_ensure() -> None:
    """Chamado pelo poller: verifica/cria os templates a cada 6 h (30 min apos falha)."""
    with _LOCK:
        if time.monotonic() < _STATE["next"]:
            return
    settings = get_settings()
    cfg: Optional[dict[str, Any]] = repos.get_config(settings.installation_id)
    if (
        not cfg
        or cfg.get("status") != "CONNECTED"
        or not cfg.get("waba_id")
        or not cfg.get("access_token_enc")
    ):
        with _LOCK:
            _STATE["next"] = time.monotonic() + 60
        return
    ok = ensure_document_templates(cfg)
    with _LOCK:
        _STATE["next"] = time.monotonic() + (_INTERVAL_OK_SECONDS if ok else _INTERVAL_FAIL_SECONDS)
