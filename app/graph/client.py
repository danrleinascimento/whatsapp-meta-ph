"""Cliente Graph API WhatsApp Cloud API (v25.0)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("whatsmeta.graph")


class GraphError(Exception):
    def __init__(
        self,
        message: str,
        *,
        http_status: int = 0,
        error_code: Optional[str] = None,
        raw: Any = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.error_code = error_code
        self.raw = raw


def _base_url(version: Optional[str] = None) -> str:
    ver = version or get_settings().graph_api_version
    return f"https://graph.facebook.com/{ver}"


def _parse_error(resp: httpx.Response) -> GraphError:
    code = None
    msg = f"HTTP {resp.status_code}"
    raw: Any = None
    try:
        raw = resp.json()
        err = raw.get("error") if isinstance(raw, dict) else None
        if isinstance(err, dict):
            msg = str(err.get("message") or msg)
            if err.get("code") is not None:
                code = str(err.get("code"))
    except Exception:
        msg = resp.text[:500] or msg
    return GraphError(msg, http_status=resp.status_code, error_code=code, raw=raw)


def upload_pdf(
    *,
    phone_number_id: str,
    access_token: str,
    file_path: Path,
    timeout: float = 120.0,
) -> str:
    """POST /{PHONE_NUMBER_ID}/media — retorna media_id."""
    url = f"{_base_url()}/{phone_number_id}/media"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "messaging_product": "whatsapp",
        "type": "application/pdf",
    }
    with file_path.open("rb") as fh:
        files = {"file": (file_path.name, fh, "application/pdf")}
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, data=data, files=files)
    if resp.status_code >= 400:
        raise _parse_error(resp)
    result = resp.json()
    media_id = result.get("id") if isinstance(result, dict) else None
    if not media_id:
        raise GraphError("Upload media sem id", http_status=resp.status_code, raw=result)
    return str(media_id)


def send_message(
    *,
    phone_number_id: str,
    access_token: str,
    payload: dict[str, Any],
    timeout: float = 60.0,
) -> dict[str, Any]:
    """POST /{PHONE_NUMBER_ID}/messages."""
    url = f"{_base_url()}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise _parse_error(resp)
    data = resp.json()
    return data if isinstance(data, dict) else {"raw": data}


def extract_message_id(graph_response: dict[str, Any]) -> Optional[str]:
    messages = graph_response.get("messages")
    if isinstance(messages, list) and messages:
        mid = messages[0].get("id") if isinstance(messages[0], dict) else None
        return str(mid) if mid else None
    return None


def build_text_payload(to: str, body: str) -> dict[str, Any]:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }


def build_document_payload(
    to: str,
    *,
    media_id: str,
    caption: Optional[str] = None,
    filename: Optional[str] = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {"id": media_id}
    if caption:
        doc["caption"] = caption
    if filename:
        doc["filename"] = filename
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "document",
        "document": doc,
    }


def build_template_payload(
    to: str,
    *,
    template_name: str,
    language_code: str = "pt_BR",
    components: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    tpl: dict[str, Any] = {
        "name": template_name,
        "language": {"code": language_code},
    }
    if components:
        tpl["components"] = components
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": tpl,
    }
