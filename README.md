# WhatsApp Meta PH (hub + agente WHATSPH)

Codigo: `C:\projetos\python\whatsmeta`  
GitHub: https://github.com/danrleinascimento/whatsapp-meta-ph  
Hub DO: https://whatsapp-meta-ph-wzewk.ondigitalocean.app  

Um unico codigo; o papel e escolhido por `APP_ROLE`:

| APP_ROLE | Onde | Funcao |
|----------|------|--------|
| `hub` | DigitalOcean | Webhook Meta, persistencia, pull de eventos, Embedded Signup |
| `agent` | PC do escritorio `127.0.0.1:8765` | Envio Graph, painel ticket, poller de status |

Roteiro mestre: `ROTEIRO_COMPLETO_DESENVOLVIMENTO_WHATSAPP_META_PH.md`

## Endpoints

### Hub (`APP_ROLE=hub`)

| Metodo | Path | Funcao |
|--------|------|--------|
| GET | `/health` | Health + `db_ok` |
| GET/POST | `/webhook/whatsapp` | Verificacao + eventos Meta (HMAC) |
| GET | `/v1/hub/events` | Pull autenticado (`X-PH-Hub-Secret`) |
| POST | `/v1/hub/pairing/claim` | Agente resgata token 1x |
| POST | `/v1/hub/embedded-signup/exchange` | code → token (App Secret so no hub) |
| GET | `/onboarding?installation_id=` | Pagina Embedded Signup |

### Agente (`APP_ROLE=agent`)

| Metodo | Path | Auth |
|--------|------|------|
| GET | `/health` | — |
| GET | `/v1/whatsapp/status` | `X-PH-Api-Key` |
| POST | `/v1/whatsapp/send-template` | API key |
| POST | `/v1/whatsapp/send-text` | API key |
| POST | `/v1/whatsapp/send-document` | API key |
| POST | `/v1/whatsapp/send-batch` | API key |
| POST | `/v1/whatsapp/pairing/claim?pair_code=` | API key |
| POST | `/v1/panel/ticket` | API key (GEPH) |
| GET | `/v1/panel/messages?ticket=` | ticket HMAC |
| GET | `/?ticket=` | ticket HMAC (painel) |

## Setup agente (dev neste PC)

```powershell
cd C:\projetos\python\whatsmeta
.\.venv\Scripts\activate
pip install -r requirements.txt
# .env ja deve ter DATABASE_URL, PH_API_KEY, TOKEN_ENCRYPTION_KEY, PANEL_TICKET_SECRET
# Aplique o SQL se ainda nao aplicou:
# psql ... -f sql\001_whatsapp_ph.sql

# Seed com token Meta de teste (System User / permanente do app PH):
# No .env: META_ACCESS_TOKEN, META_PHONE_NUMBER_ID, META_WABA_ID
python scripts\seed_dev_config.py

uvicorn app.main:app --host 127.0.0.1 --port 8765
```

## Como testar (checklist)

### 1) Health + DB

```powershell
curl http://127.0.0.1:8765/health
```

Esperado: `"status":"ok"`, `"role":"agent"`, `"db_ok":true`.

### 2) Status (sem vazar token)

```powershell
curl -H "X-PH-Api-Key: SUA_PH_API_KEY" http://127.0.0.1:8765/v1/whatsapp/status
```

Esperado apos seed: `"connected":true`, `phone_number_id` preenchido, **sem** access_token.

### 3) Path guard (PDF fora do PHSFTW)

```powershell
curl -X POST http://127.0.0.1:8765/v1/whatsapp/send-document `
  -H "X-PH-Api-Key: SUA_PH_API_KEY" -H "Content-Type: application/json" `
  -d "{\"to\":\"554984110604\",\"file_path\":\"C:\\\\Windows\\\\notepad.exe\"}"
```

Esperado: HTTP **400**.

### 4) Envio template real (celular BR)

Liste os nomes **exatos** aprovados na WABA (nao confie so no curl do painel Meta):

```powershell
python scripts\list_templates.py
# ou: GET http://127.0.0.1:8765/v1/whatsapp/templates
```

Envio (o agente resolve alias `lp_`→`3p_` e valida idioma APPROVED):

```powershell
python scripts\smoke_test.py --send-template --to 5549XXXXXXXXX
# ou explicito:
python scripts\smoke_test.py --send-template --to 5549XXXXXXXXX --template 3p_direct_integration_test_template --lang en_US
```

Confira o celular e a tabela `whatsapp_message`.

**Erros Meta comuns:** `132001` = nome/idioma errados; `131058` = `hello_world` so no Public Test Number.

### 5) Painel (somente com ticket)

```powershell
python scripts\gen_panel_ticket.py ADMIN
# Abra a URL impressa no browser
```

Abrir `http://127.0.0.1:8765/` **sem** ticket deve retornar 403.

### 6) Hub (DigitalOcean)

Apos deploy com `APP_ROLE=hub`, `DATABASE_URL` do DO, `HUB_PULL_SECRET`, `META_APP_SECRET`:

- Meta continua no webhook `/webhook/whatsapp`
- Eventos ficam em `whatsapp_webhook_event`
- Agente com o mesmo `HUB_PULL_SECRET` faz poll e atualiza status (SENT/DELIVERED/READ)

### 7) Embedded Signup (FASE 5 — depende do App Meta)

1. Configurar Login for Business + Embedded Signup config no App  
2. `META_APP_ID` + `META_EMBEDDED_SIGNUP_CONFIG_ID` no hub  
3. Abrir `https://…ondigitalocean.app/onboarding?installation_id=local-dev`  
4. Apos `pair_code`, no agente: `python scripts\claim_pairing.py PAIR_CODE`

## Fases ainda humanas / externas

| Fase | Status codigo | Pendencia PH/Meta |
|------|---------------|-------------------|
| 0–4 | Implementado neste repo | Token seed no `.env`; deploy hub com pull secret |
| 5 Embedded Signup | Scaffold hub + claim | App Review / config_id Meta |
| 6 Instalador | — | Inno + NSSM |
| 7 PHVCL/GEPH | — | Cliente HTTP + ticket |
| 8 Templates piloto | — | Aprovar utility na WABA |

## Segredos

Nunca committe `.env`. Se algum secret vazou em chat, **rotacione** (App Secret Meta, senhas Postgres, API keys).
