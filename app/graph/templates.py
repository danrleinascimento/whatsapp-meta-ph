"""Templates WhatsApp — Business Management API (oficial Meta).

Fontes:
https://developers.facebook.com/docs/graph-api/reference/whats-app-business-account/message_templates/
https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/
https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.graph.client import GraphError, _base_url, _parse_error

logger = logging.getLogger("whatsmeta.graph.templates")

# Alias observado: painel Meta (curl) usa prefixo lp_; a API da WABA lista 3p_.
# So resolve o nome real via listagem; este mapa so acelera o caso de teste Meta.
_KNOWN_UI_ALIASES: dict[str, str] = {
    "lp_direct_integration_test_template": "3p_direct_integration_test_template",
}


def list_message_templates(
    *,
    waba_id: str,
    access_token: str,
    name: Optional[str] = None,
    language: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    timeout: float = 60.0,
) -> list[dict[str, Any]]:
    """GET /{WABA_ID}/message_templates — retorna lista (name, language, status, ...)."""
    url = f"{_base_url()}/{waba_id}/message_templates"
    params: dict[str, Any] = {
        "limit": limit,
        "fields": "name,language,status,category,id",
    }
    if name:
        params["name"] = name
    if language:
        params["language"] = language
    if status:
        params["status"] = status

    headers = {"Authorization": f"Bearer {access_token}"}
    out: list[dict[str, Any]] = []
    after: Optional[str] = None

    with httpx.Client(timeout=timeout) as client:
        while True:
            p = dict(params)
            if after:
                p["after"] = after
            resp = client.get(url, params=p, headers=headers)
            if resp.status_code >= 400:
                raise _parse_error(resp)
            data = resp.json() if resp.content else {}
            rows = data.get("data") if isinstance(data, dict) else None
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict):
                        out.append(row)
            paging = data.get("paging") if isinstance(data, dict) else None
            cursors = paging.get("cursors") if isinstance(paging, dict) else None
            next_after = cursors.get("after") if isinstance(cursors, dict) else None
            # Para se nao houver next link ou after
            has_next = isinstance(paging, dict) and bool(paging.get("next"))
            if not has_next or not next_after or next_after == after:
                break
            after = str(next_after)
            if len(out) >= limit:
                break

    return out


def resolve_template(
    *,
    waba_id: str,
    access_token: str,
    template_name: str,
    language_code: Optional[str] = None,
) -> dict[str, str]:
    """Resolve nome+idioma exatos APPROVED na WABA (evita erro Meta 132001).

    Retorna dict: name, language, status, category, id, resolved_from (opcional).
    """
    requested = (template_name or "").strip()
    if not requested:
        raise ValueError("template_name vazio")

    candidates = [requested]
    alias = _KNOWN_UI_ALIASES.get(requested)
    if alias and alias not in candidates:
        candidates.append(alias)

    approved: list[dict[str, Any]] = []
    for name in candidates:
        rows = list_message_templates(
            waba_id=waba_id,
            access_token=access_token,
            name=name,
            status="APPROVED",
        )
        approved.extend(rows)

    # Fallback: lista ampla e filtra por nome (e alias) caso filtro name falhe
    if not approved:
        all_rows = list_message_templates(
            waba_id=waba_id,
            access_token=access_token,
            status="APPROVED",
        )
        wanted = set(candidates)
        approved = [r for r in all_rows if (r.get("name") or "") in wanted]

    if not approved:
        # Sugestoes: listar APPROVED disponiveis
        available = list_message_templates(
            waba_id=waba_id,
            access_token=access_token,
            status="APPROVED",
            limit=50,
        )
        hint = ", ".join(
            f"{t.get('name')}({t.get('language')})" for t in available[:20]
        ) or "(nenhum APPROVED)"
        raise ValueError(
            f"Template '{requested}' nao encontrado como APPROVED nesta WABA. "
            f"Disponiveis: {hint}. "
            f"Consulte GET /{{WABA}}/message_templates (doc Meta)."
        )

    lang_req = (language_code or "").strip() or None
    if lang_req:
        match = next(
            (
                r
                for r in approved
                if str(r.get("language") or "") == lang_req
                and str(r.get("status") or "").upper() == "APPROVED"
            ),
            None,
        )
        if not match:
            langs = sorted({str(r.get("language") or "") for r in approved})
            raise ValueError(
                f"Template '{requested}' nao existe no idioma '{lang_req}' "
                f"(erro Meta 132001). Idiomas APPROVED para este nome: {langs}"
            )
    else:
        match = next(
            (r for r in approved if str(r.get("status") or "").upper() == "APPROVED"),
            approved[0],
        )

    resolved_name = str(match.get("name") or requested)
    resolved_lang = str(match.get("language") or "")
    if not resolved_lang:
        raise ValueError(f"Template '{resolved_name}' sem language na API Meta")

    result = {
        "name": resolved_name,
        "language": resolved_lang,
        "status": str(match.get("status") or ""),
        "category": str(match.get("category") or ""),
        "id": str(match.get("id") or ""),
    }
    if resolved_name != requested:
        result["resolved_from"] = requested
        logger.info(
            "Template UI/alias %s resolvido para %s (%s)",
            requested,
            resolved_name,
            resolved_lang,
        )
    return result


def pick_smoke_template(
    *,
    waba_id: str,
    access_token: str,
) -> dict[str, str]:
    """Escolhe template APPROVED para teste (evita hello_world em numero comercial).

    hello_world so funciona no Public Test Number (erro Meta 131058).
    """
    rows = list_message_templates(
        waba_id=waba_id,
        access_token=access_token,
        status="APPROVED",
        limit=50,
    )
    preferred = [
        r
        for r in rows
        if str(r.get("name") or "") != "hello_world"
        and str(r.get("status") or "").upper() == "APPROVED"
    ]
    chosen = preferred[0] if preferred else (rows[0] if rows else None)
    if not chosen:
        raise ValueError("Nenhum template APPROVED na WABA")
    return {
        "name": str(chosen.get("name")),
        "language": str(chosen.get("language")),
        "status": str(chosen.get("status") or ""),
        "category": str(chosen.get("category") or ""),
        "id": str(chosen.get("id") or ""),
    }