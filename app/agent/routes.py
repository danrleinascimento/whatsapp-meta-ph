"""Rotas HTTP do agente local (loopback)."""

from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.agent.auth import create_panel_ticket, require_api_key, verify_panel_ticket
from app.agent.schemas import (
    SendBatchRequest,
    SendDocumentRequest,
    SendTemplateRequest,
    SendTextRequest,
    TicketRequest,
)
from app.agent import send_service
from app.config import get_settings
from app.db import repos

router = APIRouter(tags=["agent"])


@router.get("/v1/whatsapp/status")
def whatsapp_status(_: str = Depends(require_api_key)) -> dict[str, Any]:
    settings = get_settings()
    cfg = repos.get_config(settings.installation_id)
    if not cfg:
        return {
            "installation_id": settings.installation_id,
            "status": "DISCONNECTED",
            "connected": False,
        }
    return {
        "installation_id": settings.installation_id,
        "status": cfg.get("status"),
        "connected": cfg.get("status") == "CONNECTED",
        "waba_id": cfg.get("waba_id"),
        "phone_number_id": cfg.get("phone_number_id"),
        "display_phone": cfg.get("display_phone"),
        "graph_api_version": cfg.get("graph_api_version"),
        "last_error": cfg.get("last_error"),
        "connected_at": str(cfg.get("connected_at") or ""),
        # NUNCA retornar access_token
    }


@router.post("/v1/whatsapp/send-template")
def api_send_template(
    body: SendTemplateRequest,
    _: str = Depends(require_api_key),
) -> dict[str, Any]:
    try:
        return send_service.send_template(
            to=body.to,
            template_name=body.template_name,
            language_code=body.language_code,
            components=body.components,
            sistema_origem=body.sistema_origem,
            usuario_geph=body.usuario_geph,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/v1/whatsapp/send-text")
def api_send_text(
    body: SendTextRequest,
    _: str = Depends(require_api_key),
) -> dict[str, Any]:
    try:
        return send_service.send_text(
            to=body.to,
            body=body.body,
            sistema_origem=body.sistema_origem,
            usuario_geph=body.usuario_geph,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/v1/whatsapp/send-document")
def api_send_document(
    body: SendDocumentRequest,
    _: str = Depends(require_api_key),
) -> dict[str, Any]:
    try:
        return send_service.send_document(
            to=body.to,
            file_path=body.file_path,
            caption=body.caption,
            diretorio_principal=body.diretorio_principal,
            diretorio_secundario=body.diretorio_secundario,
            sistema_origem=body.sistema_origem,
            usuario_geph=body.usuario_geph,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/v1/whatsapp/send-batch")
def api_send_batch(
    body: SendBatchRequest,
    _: str = Depends(require_api_key),
) -> dict[str, Any]:
    try:
        return send_service.send_batch([item.model_dump() for item in body.items])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/v1/panel/ticket")
def api_create_ticket(
    body: TicketRequest,
    _: str = Depends(require_api_key),
) -> dict[str, str]:
    """GEPH chama isto (com API key) e abre o browser com o ticket."""
    ticket = create_panel_ticket(body.usuario_geph)
    port = get_settings().port
    return {
        "ticket": ticket,
        "panel_url": f"http://127.0.0.1:{port}/?ticket={quote(ticket, safe='')}",
    }


@router.post("/v1/whatsapp/pairing/claim")
def api_pairing_claim(
    pair_code: str = Query(...),
    _: str = Depends(require_api_key),
) -> dict[str, Any]:
    """Agente baixa o blob de pairing do hub e grava token cifrado."""
    import httpx
    from app.crypto import encrypt_token

    settings = get_settings()
    if not settings.hub_base_url or not settings.hub_pull_secret:
        raise HTTPException(status_code=500, detail="HUB_BASE_URL/HUB_PULL_SECRET ausentes")
    url = settings.hub_base_url.rstrip("/") + "/v1/hub/pairing/claim"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            url,
            params={"pair_code": pair_code, "installation_id": settings.installation_id},
            headers={"X-PH-Hub-Secret": settings.hub_pull_secret},
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="Hub nao retornou access_token")
    repos.upsert_config(
        settings.installation_id,
        status="CONNECTED",
        waba_id=data.get("waba_id"),
        phone_number_id=data.get("phone_number_id"),
        display_phone=data.get("display_phone"),
        graph_api_version=data.get("graph_api_version") or settings.graph_api_version,
        access_token_enc=encrypt_token(token),
        last_error=None,
    )
    return {
        "ok": True,
        "status": "CONNECTED",
        "waba_id": data.get("waba_id"),
        "phone_number_id": data.get("phone_number_id"),
        "display_phone": data.get("display_phone"),
    }


@router.get("/v1/panel/messages")
def api_panel_messages(
    ticket: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    usuario = verify_panel_ticket(ticket)
    settings = get_settings()
    rows = repos.list_messages(settings.installation_id, limit=limit)
    # Serializar timestamps
    out = []
    for r in rows:
        item = dict(r)
        for k in ("created_at", "updated_at"):
            if item.get(k) is not None:
                item[k] = str(item[k])
        out.append(item)
    return {"usuario_geph": usuario, "messages": out}


@router.get("/", response_class=HTMLResponse)
def panel_home(ticket: Optional[str] = Query(None)) -> HTMLResponse:
    if not ticket:
        return HTMLResponse(
            content=_page_blocked(),
            status_code=403,
        )
    try:
        usuario = verify_panel_ticket(ticket)
    except HTTPException:
        return HTMLResponse(content=_page_blocked(expired=True), status_code=403)
    return HTMLResponse(content=_page_panel(usuario=usuario, ticket=ticket))


def _page_blocked(expired: bool = False) -> str:
    motivo = "Ticket expirado ou invalido." if expired else "Abra o painel pelo sistema PH (GEPH)."
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>WHATSPH</title>
<style>
body{{font-family:Segoe UI,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;
align-items:center;justify-content:center;min-height:100vh;margin:0}}
.box{{max-width:420px;padding:2rem;border:1px solid #334155;border-radius:8px;background:#1e293b}}
h1{{font-size:1.25rem;margin:0 0 .75rem}}
p{{margin:0;color:#94a3b8;line-height:1.5}}
</style></head><body><div class="box">
<h1>WHATSPH</h1>
<p>{motivo}</p>
<p style="margin-top:1rem">Nao e permitido abrir o painel manualmente sem ticket do GEPH.</p>
</div></body></html>"""


def _page_panel(usuario: str, ticket: str) -> str:
    import json

    u = (
        usuario.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    t_js = json.dumps(ticket)
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>WHATSPH — Historico</title>
<style>
:root{{--bg:#0b1220;--card:#141c2b;--line:#243044;--text:#e8eef7;--muted:#8b9bb4;--accent:#3d8bfd}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:"Segoe UI",system-ui,sans-serif;background:radial-gradient(1200px 600px at 10% -10%,#1a2740,var(--bg));
color:var(--text);min-height:100vh}}
header{{padding:1.25rem 1.5rem;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center}}
h1{{margin:0;font-size:1.15rem;letter-spacing:.04em}}
.meta{{color:var(--muted);font-size:.85rem}}
main{{padding:1.25rem 1.5rem}}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}}
th,td{{padding:.65rem .75rem;border-bottom:1px solid var(--line);text-align:left;font-size:.85rem;vertical-align:top}}
th{{color:var(--muted);font-weight:600;background:#101826}}
.badge{{display:inline-block;padding:.15rem .45rem;border-radius:4px;font-size:.75rem;background:#243044}}
.ok{{background:#14301f;color:#7ddea0}}.fail{{background:#3a1418;color:#f5a3a8}}
.empty{{color:var(--muted);padding:2rem;text-align:center}}
button{{background:var(--accent);color:#fff;border:0;padding:.45rem .9rem;border-radius:4px;cursor:pointer}}
</style></head><body>
<header>
  <div><h1>WHATSPH</h1><div class="meta">Usuario: {u}</div></div>
  <button type="button" onclick="loadMsgs()">Atualizar</button>
</header>
<main>
  <div id="status" class="meta" style="margin-bottom:1rem">Carregando…</div>
  <div id="tbl"></div>
</main>
<script>
const TICKET = {t_js};
function esc(s) {{
  return String(s == null ? '' : s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}}
async function loadMsgs() {{
  const st = document.getElementById('status');
  const tbl = document.getElementById('tbl');
  st.textContent = 'Carregando…';
  try {{
    const r = await fetch('/v1/panel/messages?ticket=' + encodeURIComponent(TICKET) + '&limit=100');
    if (!r.ok) {{ st.textContent = 'Erro ' + r.status; return; }}
    const data = await r.json();
    const rows = data.messages || [];
    st.textContent = rows.length + ' mensagem(ns)';
    if (!rows.length) {{ tbl.innerHTML = '<div class="empty">Nenhum envio ainda.</div>'; return; }}
    let html = '<table><thead><tr><th>ID</th><th>Quando</th><th>Tipo</th><th>Destino</th><th>Status</th><th>Usuario</th><th>Host</th><th>PDF / Erro</th></tr></thead><tbody>';
    for (const m of rows) {{
      const cls = (m.status === 'FAILED') ? 'fail' : (m.status === 'ACCEPTED' || m.status === 'DELIVERED' || m.status === 'READ' || m.status === 'SENT') ? 'ok' : '';
      const err = m.error_message ? (m.error_code ? m.error_code + ': ' : '') + m.error_message : (m.local_file_path || '');
      html += '<tr>' +
        '<td>' + esc(m.id) + '</td>' +
        '<td>' + esc(m.created_at) + '</td>' +
        '<td>' + esc(m.msg_type) + '</td>' +
        '<td>' + esc(m.to_wa_id) + '</td>' +
        '<td><span class="badge ' + cls + '">' + esc(m.status) + '</span></td>' +
        '<td>' + esc(m.usuario_geph) + '</td>' +
        '<td>' + esc(m.hostname) + '</td>' +
        '<td style="max-width:280px;word-break:break-all">' + esc(err) + '</td>' +
        '</tr>';
    }}
    html += '</tbody></table>';
    tbl.innerHTML = html;
  }} catch (e) {{
    st.textContent = 'Falha: ' + e;
  }}
}}
loadMsgs();
setInterval(loadMsgs, 15000);
</script>
</body></html>"""
