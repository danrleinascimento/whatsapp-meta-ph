"""APIs do hub (DigitalOcean): pull de eventos + pairing + Embedded Signup scaffold."""

from __future__ import annotations

import hmac
import html
import json
import logging
import secrets
import time
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import repos

logger = logging.getLogger("whatsmeta.hub")

router = APIRouter(tags=["hub"])

# Pairing blobs em memoria (TTL curto). Single worker DO na v1.
_PAIRING: dict[str, dict[str, Any]] = {}
_PAIRING_TTL_SECONDS = 600


def require_hub_secret(
    x_ph_hub_secret: Optional[str] = Header(None, alias="X-PH-Hub-Secret"),
) -> str:
    expected = get_settings().hub_pull_secret
    if not expected:
        raise HTTPException(status_code=500, detail="HUB_PULL_SECRET nao configurado")
    if not x_ph_hub_secret or not hmac.compare_digest(x_ph_hub_secret, expected):
        raise HTTPException(status_code=401, detail="Hub secret invalido")
    return x_ph_hub_secret


@router.get("/v1/hub/events")
def pull_events(
    since: int = Query(0, ge=0),
    waba_id: str = Query(..., min_length=1, description="WABA do escritorio (obrigatorio)"),
    limit: int = Query(100, ge=1, le=500),
    _: str = Depends(require_hub_secret),
) -> dict[str, Any]:
    rows = repos.hub_list_events(waba_id=waba_id, since_id=since, limit=limit)
    events = []
    for r in rows:
        item = {
            "id": r["id"],
            "waba_id": r.get("waba_id"),
            "field_name": r.get("field_name"),
            "payload_json": r.get("payload_json"),
            "received_at": str(r.get("received_at") or ""),
        }
        events.append(item)
    next_since = events[-1]["id"] if events else since
    return {"events": events, "next_since": next_since}


@router.post("/v1/hub/migrate")
def hub_migrate(_: str = Depends(require_hub_secret)) -> dict[str, Any]:
    """Aplica sql/001+002 no Postgres do hub (mesmo codigo do GitHub)."""
    from app.db.migrate import apply_sql_files, HUB_SQL_FILES
    from app.db.repos import invalidate_schema_cache

    result = apply_sql_files(HUB_SQL_FILES)
    invalidate_schema_cache()
    return result


class PairingStoreRequest(BaseModel):
    installation_id: str = Field(..., min_length=1, max_length=64)
    waba_id: str
    phone_number_id: str
    access_token: str
    display_phone: Optional[str] = None
    graph_api_version: str = "v25.0"


def _store_pairing_blob(
    *,
    pair_code: str,
    installation_id: str,
    waba_id: Optional[str],
    phone_number_id: Optional[str],
    access_token: str,
    display_phone: Optional[str],
    graph_api_version: str,
) -> None:
    expires_ts = time.time() + _PAIRING_TTL_SECONDS
    import datetime as _dt

    expires_at = _dt.datetime.utcfromtimestamp(expires_ts)
    try:
        repos.pairing_store_db(
            pair_code=pair_code,
            installation_id=installation_id,
            waba_id=waba_id,
            phone_number_id=phone_number_id,
            access_token=access_token,
            display_phone=display_phone,
            graph_api_version=graph_api_version,
            expires_at=expires_at,
        )
        return
    except Exception:
        logger.exception("Pairing DB indisponivel — fallback memoria")
    _PAIRING[pair_code] = {
        "installation_id": installation_id,
        "waba_id": waba_id,
        "phone_number_id": phone_number_id,
        "access_token": access_token,
        "display_phone": display_phone,
        "graph_api_version": graph_api_version,
        "expires_at": expires_ts,
        "claimed": False,
    }


@router.post("/v1/hub/pairing/store")
def pairing_store(
    body: PairingStoreRequest,
    _: str = Depends(require_hub_secret),
) -> dict[str, str]:
    """Armazena blob temporario apos Embedded Signup."""
    code = secrets.token_urlsafe(24)
    _store_pairing_blob(
        pair_code=code,
        installation_id=body.installation_id,
        waba_id=body.waba_id,
        phone_number_id=body.phone_number_id,
        access_token=body.access_token,
        display_phone=body.display_phone,
        graph_api_version=body.graph_api_version,
    )
    return {"pair_code": code}


@router.post("/v1/hub/pairing/claim")
def pairing_claim(
    pair_code: str = Query(...),
    installation_id: str = Query(...),
    _: str = Depends(require_hub_secret),
) -> dict[str, Any]:
    """Agente local busca o token uma unica vez."""
    try:
        data = repos.pairing_claim_db(pair_code, installation_id)
        if data is not None:
            err = data.get("__error__")
            if err == "claimed":
                raise HTTPException(status_code=410, detail="pair_code ja utilizado")
            if err == "expired":
                raise HTTPException(status_code=410, detail="pair_code expirado")
            if err == "installation":
                raise HTTPException(status_code=403, detail="installation_id nao confere")
            return data
    except HTTPException:
        raise
    except Exception:
        logger.debug("Pairing claim DB falhou — tenta memoria", exc_info=True)

    blob = _PAIRING.get(pair_code)
    if not blob:
        raise HTTPException(status_code=404, detail="pair_code invalido ou expirado")
    if blob.get("claimed"):
        raise HTTPException(status_code=410, detail="pair_code ja utilizado")
    if time.time() > float(blob.get("expires_at") or 0):
        _PAIRING.pop(pair_code, None)
        raise HTTPException(status_code=410, detail="pair_code expirado")
    if blob.get("installation_id") != installation_id:
        raise HTTPException(status_code=403, detail="installation_id nao confere")
    data = dict(blob)
    _PAIRING.pop(pair_code, None)
    data.pop("claimed", None)
    data.pop("expires_at", None)
    return data


class ExchangeCodeRequest(BaseModel):
    code: str
    installation_id: str
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    display_phone: Optional[str] = None


@router.post("/v1/hub/embedded-signup/exchange")
def exchange_embedded_signup(body: ExchangeCodeRequest) -> dict[str, Any]:
    """Troca code do Embedded Signup por business token (App Secret so no hub).

    Doc: https://developers.facebook.com/docs/whatsapp/embedded-signup/implementation/
    """
    settings = get_settings()
    if not settings.meta_app_id or not settings.meta_app_secret:
        raise HTTPException(
            status_code=500,
            detail="META_APP_ID / META_APP_SECRET nao configurados no hub",
        )

    token_url = f"https://graph.facebook.com/{settings.graph_api_version}/oauth/access_token"
    params = {
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "code": body.code,
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(token_url, params=params)
    except Exception as exc:
        logger.exception("Falha exchange code")
        raise HTTPException(status_code=502, detail=f"Falha Graph: {exc}") from exc

    data = resp.json() if resp.content else {}
    if resp.status_code >= 400:
        logger.error("Exchange falhou: %s", data)
        raise HTTPException(status_code=400, detail=data)

    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Sem access_token na resposta")

    # Subscribed apps (se WABA informado)
    if body.waba_id:
        sub_url = (
            f"https://graph.facebook.com/{settings.graph_api_version}/"
            f"{body.waba_id}/subscribed_apps"
        )
        try:
            with httpx.Client(timeout=30.0) as client:
                sub = client.post(
                    sub_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
            logger.info("subscribed_apps status=%s body=%s", sub.status_code, sub.text[:300])
        except Exception:
            logger.exception("Falha subscribed_apps")

    pair_code = secrets.token_urlsafe(24)
    _store_pairing_blob(
        pair_code=pair_code,
        installation_id=body.installation_id,
        waba_id=body.waba_id,
        phone_number_id=body.phone_number_id,
        access_token=access_token,
        display_phone=body.display_phone,
        graph_api_version=settings.graph_api_version,
    )
    return {
        "ok": True,
        "pair_code": pair_code,
        "message": "Token obtido. Agente deve claim com HUB_PULL_SECRET.",
    }


@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(
    installation_id: str = Query("local-dev"),
) -> HTMLResponse:
    """Pagina HTTPS Embedded Signup (JS SDK). Requer META_APP_ID + config_id no App Meta."""
    settings = get_settings()
    app_id = settings.meta_app_id or ""
    config_id = settings.meta_embedded_signup_config_id or ""
    safe_inst = html.escape(installation_id, quote=True)
    js_inst = json.dumps(installation_id)
    js_app = json.dumps(app_id)
    js_cfg = json.dumps(config_id)
    html_page = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Conectar WhatsApp — PH Softwares</title>
<style>
body{{font-family:Segoe UI,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;
display:flex;align-items:center;justify-content:center;min-height:100vh}}
.card{{max-width:480px;padding:2rem;background:#1e293b;border:1px solid #334155;border-radius:10px}}
h1{{font-size:1.35rem;margin:0 0 .5rem}}
p{{color:#94a3b8;line-height:1.5}}
button{{margin-top:1rem;background:#1877f2;color:#fff;border:0;padding:.7rem 1.2rem;
border-radius:6px;font-size:1rem;cursor:pointer}}
code{{background:#0f172a;padding:.15rem .35rem;border-radius:4px}}
#msg{{margin-top:1rem;font-size:.9rem}}
</style>
<script async defer crossorigin="anonymous" src="https://connect.facebook.net/en_US/sdk.js"></script>
</head><body><div class="card">
<h1>Conectar conta WhatsApp</h1>
<p>Escritório: <code>{safe_inst}</code></p>
<p>Entre com a conta WhatsApp Business da empresa. Dados sensíveis ficam só no servidor da PH Softwares — nunca no computador do escritório.</p>
<button type="button" onclick="launchWhatsAppSignup()">Conectar conta WhatsApp</button>
<div id="msg"></div>
</div>
<script>
const INSTALLATION_ID = {js_inst};
const APP_ID = {js_app};
const CONFIG_ID = {js_cfg};
window.fbAsyncInit = function() {{
  FB.init({{ appId: APP_ID, autoLogAppEvents: true, xfbml: true, version: 'v25.0' }});
}};
function launchWhatsAppSignup() {{
  const msg = document.getElementById('msg');
  if (!APP_ID || !CONFIG_ID) {{
    msg.textContent = 'Cadastro WhatsApp ainda não está liberado no servidor. Fale com o suporte PH Softwares.';
    return;
  }}
  FB.login(function(response) {{
    if (response.authResponse && response.authResponse.code) {{
      msg.textContent = 'Finalizando a conexão…';
      fetch('/v1/hub/embedded-signup/exchange', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{
          code: response.authResponse.code,
          installation_id: INSTALLATION_ID,
          waba_id: window.__WA_WABA_ID || null,
          phone_number_id: window.__WA_PHONE_ID || null
        }})
      }}).then(r => r.json()).then(d => {{
        msg.textContent = d.ok
          ? ('Conta conectada. Código de vinculação: ' + d.pair_code + '. O serviço do escritório conclui o resto automaticamente.')
          : (d.detail || d.message || 'Não foi possível concluir a conexão. Tente novamente.');
      }}).catch(e => {{ msg.textContent = 'Falha na conexão: ' + String(e); }});
    }} else {{
      msg.textContent = 'Conexão cancelada ou incompleta. Tente novamente.';
    }}
  }}, {{
    config_id: CONFIG_ID,
    response_type: 'code',
    override_default_response_type: true,
    extras: {{
      setup: {{}},
      featureType: 'whatsapp_business_app_onboarding',
      sessionInfoVersion: '3'
    }}
  }});
}}
window.addEventListener('message', (event) => {{
  if (!event.origin.endsWith('facebook.com')) return;
  try {{
    const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
    if (data && data.type === 'WA_EMBEDDED_SIGNUP') {{
      if (data.data) {{
        window.__WA_WABA_ID = data.data.waba_id;
        window.__WA_PHONE_ID = data.data.phone_number_id;
      }}
    }}
  }} catch (e) {{}}
}});
</script>
</body></html>"""
    return HTMLResponse(content=html_page)
