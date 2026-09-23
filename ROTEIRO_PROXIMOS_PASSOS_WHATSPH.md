# Roteiro — Próximos Passos WHATSPH

**Data revisão:** 22/09/2026 17:57 (UTC-3)  
**Projeto:** `C:\projetos\python\whatsmeta`  
**GitHub:** https://github.com/danrleinascimento/whatsapp-meta-ph (`main`, commit `ed859f2`, app **v0.2.3**)  
**Hub DO:** https://whatsapp-meta-ph-wzewk.ondigitalocean.app  
**PHVCL:** `C:\CBuilder5\Projects\Lib\phvcl`  
**GEPH:** `C:\CBuilder5\Projects\GEPH`  
**Regra:** só APIs oficiais Meta. App Secret **somente** no hub DO. Fontes C++ = **CP1252** (`REGRA_CODIFICACAO.md`).

Documento irmão: `ROTEIRO_COMPLETO_DESENVOLVIMENTO_WHATSAPP_META_PH.md`.  
Checklist DO: `docs/CHECKLIST_HUB_DIGITALOCEAN.md`.  
PHVCL: `docs/INTEGRACAO_PHVCL_WHATSMETA.md`.  
**Produção instalador + GEPH (início→fim):** `ROTEIRO_PRODUCAO_INSTALADOR_GEPH_PHVCL.md`.

---

## 0. Estado comprovado (evidência 22/09/2026)

| Item | Status | Evidência |
|------|--------|-----------|
| GitHub `main` | **OK** | `ed859f2` — migrate hub + React panel + SQL 002/003 |
| Hub `/health` | **OK** | `role=hub` `version=0.2.3` `db_ok=true` |
| Hub schema Postgres | **Falha CREATE** | `schema_ok=false` — Dev DB user sem CREATE em `public` |
| Hub eventos | **Fallback memória** | `events_backend=memory` — poller `200 OK` (não mais 500) |
| `DATABASE_URL` DO | **OK** | `${whatsapp-meta-db.DATABASE_URL}` (não usar `dev-db-085123`) |
| `HUB_PULL_SECRET` DO | **OK** | alinhado ao `.env` local — events autenticados |
| `META_APP_SECRET` / verify token DO | **OK** | Encrypted |
| `META_APP_ID` | **Confirmado** | `2053406131958490` (Meta Basic) — conferir se já está no env DO |
| Agente local `:8765` | **OK** | `role=agent` `db_ok=true` `schema_ok=true` |
| Poller → hub | **OK** | `GET /v1/hub/events` → `HTTP/1.1 200 OK` |
| Seed / CONECTADO | **OK** | WABA `2147274472541752` telefone `+554984110604` |
| Template smoke 17:54 | **OK envio** | `ACCEPTED` `3p_direct_integration_test_template` → `5549998185612` |
| Status DELIVERED no painel (msg nova) | **Pendente / parcial** | Painel mostra ACCEPTED; msgs antigas READ/DELIVERED existem |
| PDF Cloud API | **OK** (teste manhã) | `Orcamento-5822371` ACCEPTED |
| Painel React Vite | **OK** | ticket GEPH, filtros, Conectado |
| `META_EMBEDDED_SIGNUP_CONFIG_ID` | **Não criado** | N4 |
| Instalador `.exe` | **Rascunho** | `installer/WHATSPH.iss` — falta empacotar `dist\whatsph` |
| PHVCL código | **No disco** | `WhatsMetaClient` + `SenWA` + `USEUNIT` + `PH.bpk` |
| `WhatsMetaClient.obj` / `PH.bpl` | **Existem** em `Lib\bpl` | Validar no BCB5 se GEPH linka sem Unresolved |
| Menu GEPH / painel pelo GEPH | **Pendente** | N6.2 |
| Neon / doadmin (schema persistente hub) | **Recomendado** | sem isso eventos somem no redeploy do hub |

---

## Decisão de stack (congelada)

| Tema | Decisão |
|------|----------|
| Painel | **FastAPI + React Vite + Tailwind** (`web/`) — Django descartado |
| Hub | DigitalOcean App Platform `APP_ROLE=hub` |
| Agente | Windows loopback `127.0.0.1:8765` `APP_ROLE=agent` |
| Eventos hub sem CREATE | Fallback **memória** até Neon/doadmin |
| C++ | Indy → agente; **sem** App Secret no BPL |

---

## Ordem obrigatória (atualizada)

```text
N1  Hub DO                          ← FEITO (db_ok + secret); schema Postgres PENDENTE
N2  Poll status ponta a ponta       ← PARCIAL (200 OK; DELIVERED da msg 17:54 a confirmar)
N3  Painel React                    ← FEITO
N4  Embedded Signup + pairing       ← PENDENTE (produto multi-cliente)
N5  Instalador WHATSPH              ← PRÓXIMO BLOCO PRODUÇÃO WINDOWS
N6  PHVCL + GEPH                    ← PRÓXIMO BLOCO PRODUÇÃO DESKTOP
N7  Templates produto + piloto      ← após N5/N6 mínimos
```

**Ordem prática de produção agora:** N6.1b validar BPL → N5 instalador → N2 fechar DELIVERED → N4 → N7.

---

## N1 — Hub DigitalOcean

### Feito
- Binding DB: `${whatsapp-meta-db.DATABASE_URL}`
- `HUB_PULL_SECRET` + poller autenticado
- Deploy v0.2.3: migrate no startup + `POST /v1/hub/migrate` + fallback memória
- `/health`: `db_ok=true`

### Ainda aberto
1. **Schema persistente** — usuário `whatsapp-meta-db` não cria tabelas (`permission denied for schema public`). Opções:
   - Neon (ou Managed PG em região com `doadmin`) → trocar `DATABASE_URL` do App → redeploy → `schema_ok=true`
   - ou `doadmin` + `scripts/apply_sql_doadmin.py`
2. Confirmar `META_APP_ID=2053406131958490` e `GRAPH_API_VERSION=v25.0` no env do Web Service.
3. Webhook Meta callback: `https://whatsapp-meta-ph-wzewk.ondigitalocean.app/webhook/whatsapp` (campo `messages`).

### Aceite N1 completo
- [x] hub Healthy + `db_ok`
- [x] poller 200
- [ ] `schema_ok=true` **ou** aceite explícito do fallback memória em piloto interno
- [ ] status da mensagem nova evolui no painel (N2)

---

## N2 — Validação ponta a ponta

| Cenário | Status |
|---------|--------|
| A Template utility ACCEPTED | **OK** (17:54) |
| A→ DELIVERED/READ no painel | **A confirmar** (atualizar painel; ver se celular recebeu) |
| B PDF | **OK** manhã (ACCEPTED) |
| C Falhas Meta 132001 / 131058 | **OK** (aparecem no painel) |
| D Poller após restart hub | Memória zera — esperar Neon |

Se ACCEPTED não virar DELIVERED e o celular **recebeu**: webhook Meta → hub (HMAC / campo) ou evento perdido na memória. Checar Runtime Logs do App + `/health` `events_memory_count`.

---

## N3 — Painel — FEITO

Aceite: ticket `gen_panel_ticket.py` → UI React, Conectado, histórico.  
Pendente só N3.6 (abrir pelo menu GEPH).

---

## N4 — Embedded Signup (cliente conecta WABA dele)

Pendente inteiro. Bloqueia piloto multi-escritório.  
`META_APP_ID` já conhecido; falta `config_id` + OAuth redirect + App Review.

---

## N5 — Instalador Windows (produção WHATSPH) — PASSO A PASSO

**Objetivo:** técnico instala em `{PHSFTW}\WHATSPH\` sem Python “na mão”; serviço `PHWhatsMeta` sobe `:8765`.

### N5.A — Pré-requisitos (dev PH)

1. Inno Setup 6 instalado.
2. Postgres do cliente acessível (ou instalar Postgres/serviço PH já existente na porta usada pelo escritório).
3. Build do agente empacotável:

```powershell
cd C:\projetos\python\whatsmeta
# garantir web/dist atualizado
cd web; npm ci; npm run build; cd ..
# pasta de distribuição (exemplo)
mkdir dist\whatsph -Force
# copiar: app\, sql\, web\dist\, scripts\apply_sql.py, requirements.txt, installer\*.bat
# criar .venv embutido OU python embed + pip install -r requirements.txt dentro de dist\whatsph
```

4. Ajustar `installer/WHATSPH.iss`:
   - `#define MyAppVersion "0.2.3"`
   - `Source` apontando para `dist\whatsph\*`
5. Completar `installer/install_service.bat` (NSSM):
   - `nssm install PHWhatsMeta ...\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765`
   - AppDirectory = `{PHSFTW}\WHATSPH`
   - logs → `WHATSPH\logs\`
6. `apply_sql.bat`: `python scripts\apply_sql.py` com `DATABASE_URL` do cliente (DB `whatsapp_ph` local).

### N5.B — Conteúdo do `.env` gerado no 1º install

```env
APP_ROLE=agent
APP_ENV=production
BIND_HOST=127.0.0.1
PORT=8765
INSTALLATION_ID=<uuid>
DATABASE_URL=postgresql://.../whatsapp_ph
PH_API_KEY=<gerado>
TOKEN_ENCRYPTION_KEY=<gerado>
PANEL_TICKET_SECRET=<gerado>
HUB_BASE_URL=https://whatsapp-meta-ph-wzewk.ondigitalocean.app
HUB_PULL_SECRET=<mesmo do hub DO — valor de fábrica PH>
GRAPH_API_VERSION=v25.0
PHSFTW_ROOT=C:\PHSFTW
```

**Não** embutir `META_APP_SECRET` nem `META_ACCESS_TOKEN` no instalador.

### N5.C — Compilar e testar

1. Abrir `WHATSPH.iss` no Inno → Compile → `WHATSPH_Setup_0.2.3.exe`
2. Instalar em VM Win10/11 limpa (ou pasta teste)
3. Aceite:
   - [ ] Serviço `PHWhatsMeta` Running
   - [ ] `http://127.0.0.1:8765/health` → `role=agent` `db_ok=true`
   - [ ] Abrir `/?` sem ticket → 403 / tela bloqueada
   - [ ] Ticket via API → painel React

### N5.D — Entrega ao escritório

1. Rodar Setup como admin  
2. Garantir Postgres + SQL  
3. Conectar WhatsApp (hoje: seed/dev PH; produção: N4 Embedded Signup)  
4. GEPH já apontando `DiretorioPrincipal` / PHSFTW  

---

## N6 — PHVCL + GEPH (produção desktop) — PASSO A PASSO

### Premissas
- CP1252 + CRLF  
- Meta se CONECTADO; senão Whats.exe  
- Painel só com ticket HMAC  

### N6.A — Build PH.bpl (você no BCB5) — FAZER AGORA

Estado disco (22/09 17:57): `WhatsMetaClient.obj` e `PH.bpl` **existem**. Ainda assim validar no IDE:

1. Abrir `C:\CBuilder5\Projects\Lib\phvcl\PH.bpk`
2. Confirmar no Project Manager: `WhatsMetaClient.cpp`
3. **Project → Build PH** (Rebuild se linker antigo)
4. Sem `Unresolved external 'TWhatsMetaClient::...'`
5. Commit SVN PH Softwares (não misturar UTF-8): `WhatsMetaClient.*`, `SenWA.cpp`, `PH.cpp`, `PH.bpk`

### N6.B — Build GEPH

1. Abrir projeto GEPH que depende de `PH.bpl`
2. Rebuild GEPH / PH.exe  
3. Garantir runtime: serviço WHATSPH + `{PHSFTW}\WHATSPH\.env` com `PH_API_KEY`

### N6.C — Fluxos mínimos produção (código a completar)

| # | Tarefa | Status |
|---|--------|--------|
| N6.C.1 | Envio relatório SenWA → Meta → fallback Whats.exe | Código **feito** — teste no exe |
| N6.C.2 | Menu WhatsApp → Abrir painel (`CreatePanelTicket` + ShellExecute) | **Implementar** |
| N6.C.3 | Menu Status / Conectar (N4 onboarding) | Após N4 |
| N6.C.4 | Lote boletos `send-batch` | Depois do aceite SenWA |
| N6.C.5 | `PermiteEnviarWhats` | Conferir permissão existente |

### N6.D — Aceite GEPH

- [ ] Rebuild sem Unresolved `TWhatsMetaClient`
- [ ] Relatório PDF chega no WhatsApp via Meta com agente CONECTADO
- [ ] Agente parado → Whats.exe continua funcionando
- [ ] Menu abre painel com ticket (não URL crua sem ticket)

---

## N7 — Produto / piloto

Templates utility do escritório, manuais, App Review, Tech Provider — após N5+N6 mínimos e idealmente N4.

---

## Riscos atualizados

| Risco | Mitigação |
|-------|-----------|
| Dev DB sem CREATE | Neon/doadmin **ou** aceitar memória só em lab |
| Eventos memória somem no redeploy hub | Neon antes de piloto externo |
| ACCEPTED sem DELIVERED | Verificar webhook Meta + logs DO + celular |
| Encoding C++ UTF-8 | Só editar CP1252 / scripts `patch_*_cp1252.py` |
| Secret no chat/print | Rotacionar App Secret / senha DB se vazou |
| `hello_world` | Nunca em número real (131058) |

---

## Próximos passos imediatos (produção)

### Bloco A — Desktop (esta semana)
1. **BCB5:** Rebuild `PH.bpl` + Rebuild GEPH  
2. Testar envio relatório pelo form SenWA com agente rodando  
3. Implementar botão/menu **Abrir painel WHATSPH** (ticket)  
4. SVN commit PHVCL (CP1252)

### Bloco B — Instalador (em paralelo)
1. Montar `dist\whatsph` (app + venv/embed + `web\dist` + sql)  
2. NSSM em `install_service.bat`  
3. Compilar Inno `WHATSPH_Setup_0.2.3.exe`  
4. Teste VM limpa

### Bloco C — Hub persistente (antes de piloto cliente)
1. Postgres com CREATE (Neon ou doadmin)  
2. Confirmar `/health` → `schema_ok=true` `events_backend=postgres`  
3. Fechar N2: template novo → DELIVERED no painel

### Bloco D — Depois
1. N4 Embedded Signup  
2. N7 templates + manuais + piloto  

**Fim do roteiro revisado 22/09/2026 17:57.**
