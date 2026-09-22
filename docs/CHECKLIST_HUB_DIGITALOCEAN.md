# Checklist operacional — Hub DigitalOcean (N1)
# Data: 22/09/2026 (revisao 14:42)
#
# Evidencia Overview DO:
#   Database component name = whatsapp-meta-db (Dev PostgreSQL 17)
#   NAO usar mais ${dev-db-085123.DATABASE_URL} → erro "is not a valid variable"
#
# Binding correto:
#   DATABASE_URL=${whatsapp-meta-db.DATABASE_URL}

## Passo a passo (voce no painel DO)

### A) Corrigir DATABASE_URL
1. App whatsapp-meta-ph → Settings
2. Abrir Environment Variables do componente web (ou App-Level)
3. Em DATABASE_URL, apagar o valor antigo e colocar EXATAMENTE:
   ${whatsapp-meta-db.DATABASE_URL}
4. Scope: Run time (ou Run and build time)
5. A borda vermelha deve sumir

### B) Adicionar variaveis que faltam
Clicar "+ Add environment variable" e criar:

| Key | Value | Encrypt? |
|-----|-------|----------|
| HUB_PULL_SECRET | GQ_Lg0ELY-drZriuqQvgzSqJ7sUhdb00AOOq5n0zKEo | sim (recomendado) |
| META_APP_ID | 2053406131958490 | nao |
| GRAPH_API_VERSION | v25.0 | nao |

Confirmar que JA existem (nao apagar):
- APP_ENV=production
- LOG_LEVEL=INFO
- META_WEBHOOK_VERIFY_TOKEN (Encrypted)
- META_APP_SECRET (Encrypted)

### C) Salvar e redeploy
1. Save
2. Se nao auto-deployar: Activity → Redeploy / Deploy
3. Esperar Overview = Healthy

### D) SQL automatico no hub (GitHub → deploy)

A partir da v0.2.3 o hub no startup tenta aplicar `sql/001` + `sql/002`.
Se o Dev DB negar CREATE, usa **fallback em memoria** para eventos
(`events_backend=memory` no `/health`) — poller funciona ate ter doadmin/Neon.

Manual (apos deploy), com o mesmo HUB_PULL_SECRET:
```powershell
Invoke-RestMethod -Method Post `
  -Uri "https://whatsapp-meta-ph-wzewk.ondigitalocean.app/v1/hub/migrate" `
  -Headers @{ "X-PH-Hub-Secret" = "SEU_HUB_PULL_SECRET" }
```


O usuario da App (`whatsapp-meta-db`) **NAO** tem CREATE no schema `public`.
O dono do banco e `doadmin`. Sem GRANT do doadmin, `/v1/hub/events` retorna 500.

### Como obter senha doadmin
1. DigitalOcean → **Databases** (menu lateral) **ou** App → Database → Connection Details
2. Procurar usuario **doadmin** (as vezes dropdown "Users" / reset password)
3. Copiar a senha do doadmin (diferente da senha `whatsapp-meta-db`)

### Aplicar (no PC)
```powershell
cd C:\projetos\python\whatsmeta
$env:DATABASE_URL="postgresql://whatsapp-meta-db:SENHA_APP@HOST:25060/whatsapp-meta-db?sslmode=require"
$env:DOADMIN_PASSWORD="SENHA_DOADMIN"
.\.venv\Scripts\python.exe scripts\apply_sql_doadmin.py
```

### pgAdmin III (se preferir)
- Host: `app-0d1df57e-aa17-4ba2-8f2b-5ed75a80f685-do-user-43012931-0.e.db.ondigitalocean.com` (completo!)
- Port: 25060
- Username: `doadmin` (para criar tabelas) ou `whatsapp-meta-db` (so leitura depois)
- Maintenance DB: `whatsapp-meta-db`
- Aba SSL: mode = **require**
- Depois rode 001 + 002 (+ 003 opcional) como doadmin


### E) Testar health
Abrir no browser:
https://whatsapp-meta-ph-wzewk.ondigitalocean.app/health

Esperado:
{"status":"ok","role":"hub","db_ok":true,...}

Se db_ok ainda false: SQL nao aplicado ou DATABASE_URL ainda errado.

### F) Agente local (ja deve estar alinhado)
No .env local:
HUB_BASE_URL=https://whatsapp-meta-ph-wzewk.ondigitalocean.app
HUB_PULL_SECRET=GQ_Lg0ELY-drZriuqQvgzSqJ7sUhdb00AOOq5n0zKEo
META_APP_ID=2053406131958490

Reiniciar uvicorn do agente.

## Meta App
- META_APP_ID: 2053406131958490
- META_EMBEDDED_SIGNUP_CONFIG_ID: ainda N4

## Nao colocar no DO
- META_ACCESS_TOKEN
- PH_API_KEY / PANEL_TICKET_SECRET / TOKEN_ENCRYPTION_KEY do escritorio
