"""APIs do hub (DigitalOcean): pull de eventos + pairing + Embedded Signup."""

from __future__ import annotations

import hmac
import html
import json
import logging
import re
import secrets
import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db import repos
from app.hub.onboarding import OnboardingError, only_digits, run_onboarding

logger = logging.getLogger("whatsmeta.hub")

router = APIRouter(tags=["hub"])

# Pairing blobs em memoria (TTL curto). Single worker DO na v1.
_PAIRING: dict[str, dict[str, Any]] = {}
_PAIRING_TTL_SECONDS = 600

# Mesmo formato aceito pelo agente (app/agent/onboarding.py).
INSTALLATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
PAIR_CODE_RE = re.compile(r"[A-Za-z0-9_-]{20,64}")


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
        _PAIRING.pop(pair_code, None)
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
    code: str = Field(..., min_length=1, max_length=4096)
    installation_id: str
    # Gerado pelo agente do escritorio (GEPH > Conectar). Sem ele: modo manual (pair_code na tela).
    pair_code: Optional[str] = None
    waba_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    # event da mensagem WA_EMBEDDED_SIGNUP (ex.: FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING).
    flow_event: Optional[str] = Field(None, max_length=64)


@router.post("/v1/hub/embedded-signup/exchange")
def exchange_embedded_signup(body: ExchangeCodeRequest) -> dict[str, Any]:
    """Troca o code do Embedded Signup e conclui o onboarding (App Secret so no hub)."""
    if not INSTALLATION_ID_RE.fullmatch(body.installation_id):
        raise HTTPException(status_code=400, detail="Identificação do escritório inválida.")
    if body.pair_code is not None and not PAIR_CODE_RE.fullmatch(body.pair_code):
        raise HTTPException(status_code=400, detail="Código de vinculação inválido.")

    try:
        result = run_onboarding(
            code=body.code,
            waba_hint=only_digits(body.waba_id),
            phone_hint=only_digits(body.phone_number_id),
            flow_event=body.flow_event,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    automatic = body.pair_code is not None
    pair_code = body.pair_code or secrets.token_urlsafe(24)
    _store_pairing_blob(
        pair_code=pair_code,
        installation_id=body.installation_id,
        waba_id=result.waba_id,
        phone_number_id=result.phone_number_id,
        access_token=result.access_token,
        display_phone=result.display_phone,
        graph_api_version=get_settings().graph_api_version,
    )
    return {
        "ok": True,
        "automatic": automatic,
        "pair_code": None if automatic else pair_code,
        "display_phone": result.display_phone,
        "verified_name": result.verified_name,
        "coexistence": result.coexistence,
        "warnings": result.warnings,
    }


def _onboarding_invalid_page() -> HTMLResponse:
    return HTMLResponse(
        content=(
            '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
            "<title>Conectar WhatsApp — PH Softwares</title></head><body>"
            "<p>Endereço de cadastro inválido. Abra o cadastro pelo GEPH: "
            "menu WhatsApp &gt; Conectar conta WhatsApp.</p></body></html>"
        ),
        status_code=400,
    )


def _js(value: Any) -> str:
    """Valor JSON seguro dentro de <script> (sem '</' nem '<!--')."""
    return json.dumps(value).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(
    installation_id: str = Query("local-dev"),
    pair_code: Optional[str] = Query(None),
) -> HTMLResponse:
    """Pagina HTTPS do Embedded Signup (JS SDK) com coexistencia do app WhatsApp Business."""
    if not INSTALLATION_ID_RE.fullmatch(installation_id):
        return _onboarding_invalid_page()
    if pair_code is not None and not PAIR_CODE_RE.fullmatch(pair_code):
        return _onboarding_invalid_page()
    settings = get_settings()
    page = (
        _ONBOARDING_HTML.replace("__INSTALLATION_HTML__", html.escape(installation_id, quote=True))
        .replace("__INSTALLATION_JS__", _js(installation_id))
        .replace("__PAIR_CODE_JS__", _js(pair_code))
        .replace("__APP_ID_JS__", _js(settings.meta_app_id or ""))
        .replace("__CONFIG_ID_JS__", _js(settings.meta_embedded_signup_config_id or ""))
        .replace("__GRAPH_VERSION_JS__", _js(settings.graph_api_version))
    )
    return HTMLResponse(content=page)


_ONBOARDING_HTML = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Conectar WhatsApp — PH Softwares</title>
<style>
body{font-family:Segoe UI,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;
display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{max-width:540px;margin:1rem;padding:2rem;background:#1e293b;border:1px solid #334155;border-radius:10px}
h1{font-size:1.35rem;margin:0 0 .5rem}
p,li{color:#94a3b8;line-height:1.5}
ol{padding-left:1.2rem}
button{margin-top:1rem;background:#1877f2;color:#fff;border:0;padding:.7rem 1.2rem;
border-radius:6px;font-size:1rem;cursor:pointer}
button:disabled{opacity:.6;cursor:default}
code{background:#0f172a;padding:.15rem .35rem;border-radius:4px}
a{color:#93c5fd}
#msg{margin-top:1rem;font-size:.95rem}
#msg p{color:#e2e8f0;margin:.4rem 0}
#msg.erro p{color:#fca5a5}
#msg .aviso{color:#fcd34d}
</style>
<script async defer crossorigin="anonymous" src="https://connect.facebook.net/en_US/sdk.js"></script>
</head><body><div class="card">
<h1>Conectar conta WhatsApp</h1>
<p>Escritório: <code>__INSTALLATION_HTML__</code></p>
<p>Use o número que o escritório já usa no app <b>WhatsApp Business</b>. O app continua funcionando normalmente no celular.</p>
<ol>
<li>Deixe o celular com o WhatsApp Business por perto, com o app aberto.</li>
<li>Clique no botão abaixo e entre com o Facebook de quem administra a empresa.</li>
<li>Escolha conectar a conta existente do WhatsApp Business e informe o número.</li>
<li>No celular, toque em <b>Conectar</b> na mensagem recebida, confirme o compartilhamento do histórico de conversas e copie o código para a janela da Meta.</li>
</ol>
<button type="button" id="btn" onclick="launchWhatsAppSignup()">Conectar conta WhatsApp</button>
<div id="msg"></div>
</div>
<script>
const INSTALLATION_ID = __INSTALLATION_JS__;
const PAIR_CODE = __PAIR_CODE_JS__;
const APP_ID = __APP_ID_JS__;
const CONFIG_ID = __CONFIG_ID_JS__;
const GRAPH_VERSION = __GRAPH_VERSION_JS__;
const signup = { event: null, waba_id: null, phone_number_id: null };

window.fbAsyncInit = function() {
  FB.init({ appId: APP_ID, autoLogAppEvents: true, xfbml: true, version: GRAPH_VERSION });
};

function show(lines, isError) {
  const box = document.getElementById('msg');
  box.className = isError ? 'erro' : '';
  box.textContent = '';
  for (const line of lines) {
    if (!line) continue;
    const p = document.createElement('p');
    if (typeof line === 'string') { p.textContent = line; }
    else if (line.aviso) { p.className = 'aviso'; p.textContent = line.aviso; }
    else if (line.link) {
      p.appendChild(document.createTextNode(line.text + ' '));
      const a = document.createElement('a');
      a.href = line.link; a.target = '_blank'; a.rel = 'noopener'; a.textContent = line.linkText;
      p.appendChild(a);
    }
    box.appendChild(p);
  }
}

function setBusy(busy) { document.getElementById('btn').disabled = busy; }

window.addEventListener('message', (event) => {
  if (!event.origin.endsWith('facebook.com')) return;
  let data = event.data;
  try { data = typeof data === 'string' ? JSON.parse(data) : data; } catch (e) { return; }
  if (!data || data.type !== 'WA_EMBEDDED_SIGNUP') return;
  const d = data.data || {};
  signup.event = data.event || null;
  if (d.waba_id) signup.waba_id = String(d.waba_id);
  if (d.phone_number_id) signup.phone_number_id = String(d.phone_number_id);
  if (data.event === 'CANCEL') {
    setBusy(false);
    if (d.error_message) {
      show(['A Meta informou um erro no cadastro: ' + d.error_message
        + (d.error_code ? ' (código ' + d.error_code + ')' : '') + '.',
        'Corrija o que foi pedido e clique no botão para tentar de novo.'], true);
    } else {
      show(['O cadastro foi fechado antes do fim. Clique no botão para tentar de novo.'], true);
    }
  }
});

function success(d) {
  const lines = [];
  const conta = [d.verified_name, d.display_phone].filter(Boolean).join(' — ');
  lines.push('Conta WhatsApp conectada' + (conta ? ': ' + conta : '') + '.');
  if (d.automatic) {
    lines.push('O sistema PH deste escritório conclui a configuração sozinho em até 1 minuto. '
      + 'Depois disso, a Situação do WhatsApp no GEPH mostra a conta conectada. Pode fechar esta página.');
  } else {
    lines.push('Código de vinculação (vale 10 minutos): ' + d.pair_code);
  }
  if (d.coexistence) {
    lines.push('O WhatsApp Business continua funcionando no celular. Deixe o app aberto por alguns minutos para terminar a sincronização.');
  }
  lines.push({ text: 'Para enviar boletos a quem não conversou com o escritório nas últimas 24 horas, a Meta cobra por mensagem: '
    + 'cadastre uma forma de pagamento no WhatsApp Manager (Visão geral > Adicionar forma de pagamento).',
    link: 'https://business.facebook.com/wa/manage/home/', linkText: 'Abrir o WhatsApp Manager' });
  for (const w of (d.warnings || [])) lines.push({ aviso: 'Atenção: ' + w });
  show(lines, false);
}

function finish(code) {
  show(['Finalizando a conexão e sincronizando com o WhatsApp Business. Mantenha o app aberto no celular; pode levar até 1 minuto…'], false);
  fetch('/v1/hub/embedded-signup/exchange', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      code: code,
      installation_id: INSTALLATION_ID,
      pair_code: PAIR_CODE,
      waba_id: signup.waba_id,
      phone_number_id: signup.phone_number_id,
      flow_event: signup.event
    })
  })
    .then(r => r.json().catch(() => ({})).then(d => ({ ok: r.ok, d: d })))
    .then(res => {
      if (res.ok && res.d.ok) { success(res.d); return; }
      setBusy(false);
      const detail = typeof res.d.detail === 'string' ? res.d.detail : 'Não foi possível concluir a conexão.';
      show([detail, 'Se o problema continuar, fale com o suporte da PH Softwares.'], true);
    })
    .catch(e => {
      setBusy(false);
      show(['Falha de comunicação com o servidor da PH Softwares: ' + String(e)], true);
    });
}

function launchWhatsAppSignup() {
  if (!APP_ID || !CONFIG_ID) {
    show(['O cadastro do WhatsApp ainda não está liberado no servidor da PH Softwares. Fale com o suporte.'], true);
    return;
  }
  if (typeof FB === 'undefined') {
    show(['A página ainda está carregando o login da Meta. Aguarde alguns segundos e clique de novo.'], true);
    return;
  }
  signup.event = null; signup.waba_id = null; signup.phone_number_id = null;
  setBusy(true);
  show(['Siga as instruções na janela da Meta…'], false);
  FB.login(function(response) {
    if (response && response.authResponse && response.authResponse.code) {
      finish(response.authResponse.code);
      return;
    }
    setBusy(false);
    if (signup.event !== 'CANCEL') {
      show(['O cadastro foi fechado ou não terminou. Clique no botão para tentar de novo.'], true);
    }
  }, {
    config_id: CONFIG_ID,
    response_type: 'code',
    override_default_response_type: true,
    extras: {
      setup: {},
      featureType: 'whatsapp_business_app_onboarding',
      sessionInfoVersion: '3'
    }
  });
}
</script>
</body></html>"""
