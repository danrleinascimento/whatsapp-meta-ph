# Roteiro — Próximos Passos WHATSPH (pós envio template+PDF OK)

**Data:** 22/09/2026  
**Projeto:** `C:\projetos\python\whatsmeta`  
**GitHub:** https://github.com/danrleinascimento/whatsapp-meta-ph (`main`)  
**Hub DO:** https://whatsapp-meta-ph-wzewk.ondigitalocean.app  
**PHVCL:** `C:\CBuilder5\Projects\Lib\phvcl`  
**GEPH:** `C:\CBuilder5\Projects\GEPH`

> **Objetivo deste documento:** checklist executável do que falta **depois** do aceite local (template + PDF Cloud API no celular).  
> Documento irmão: `ROTEIRO_COMPLETO_DESENVOLVIMENTO_WHATSAPP_META_PH.md`.  
> **Regra:** só APIs oficiais Meta. App Secret **somente** no hub DO.

---

## 0. Estado comprovado (22/09/2026 — revisao pos-prints Meta/DO)

| Item | Status |
|------|--------|
| Push GitHub (agente + hub + templates resolve) | **Feito** — ate `a2957f9` (+ painel React nesta sessao, push pendente) |
| Agente local `APP_ROLE=agent` `:8765` | **OK** |
| Seed token System User + `CONNECTED` | **OK** |
| Template APPROVED (`3p_direct_integration_test_template` / alias `lp_`) | **OK** |
| PDF `Orcamento-5822371.pdf` → WhatsApp | **OK** (`ACCEPTED`) |
| Painel ticket HMAC | **OK** |
| Painel **React + Vite + Tailwind** (`web/`) | **Feito** — `web/dist` servido pelo FastAPI |
| Meta App `PH_Softwares` / `META_APP_ID` | **Confirmado** `2053406131958490` |
| `META_EMBEDDED_SIGNUP_CONFIG_ID` | **Ainda nao criado** (N4) |
| DO `DATABASE_URL` | **OK** `${dev-db-085123.DATABASE_URL}` |
| DO `META_APP_SECRET` / `META_WEBHOOK_VERIFY_TOKEN` | **Encrypted OK** |
| DO `HUB_PULL_SECRET` | **VAZIO no DO** — colar o valor do `.env` local |
| DO `META_APP_ID` | **Adicionar** `2053406131958490` |
| SQL no Postgres DO (`001`/`002`) | **Pendente** (causa tipica de `db_ok:false`) |
| Codigo hub poller / events | **No repo** — validar apos secret + SQL |
| Embedded Signup live | **Scaffold so** |
| Instalador Windows | **Codigo Inno/NSSM** — `.exe` pendente |
| PHVCL / GEPH | **Em andamento** — falta Rebuild `PH.bpl` no BCB5 |

---

## Decisao N3 — Painel web moderno

**Pedido:** FastAPI + React Vite, moderno e bonito. **Feito.**

| Opcao | Status |
|-------|--------|
| Django + React | **Descartado** |
| **FastAPI + React Vite + Tailwind** | **Implementado** em `web/` |
| HTML legado | Fallback se `web/dist` ausente |

```powershell
cd C:\projetos\python\whatsmeta\web
npm install
npm run build
cd ..
uvicorn app.main:app --host 127.0.0.1 --port 8765
python scripts\gen_panel_ticket.py ADMIN
```

---

## Onde encontrar `META_APP_ID` e `config_id` (N4)

1. Meta Developers → App **PH_Softwares** → Configuracoes → Basico.
2. **ID do Aplicativo** = `META_APP_ID` = **`2053406131958490`** (confirmado print 22/09/2026).
3. `META_EMBEDDED_SIGNUP_CONFIG_ID`: criar Embedded Signup (ainda nao existe) e copiar Configuration ID.
4. OAuth Redirect: `https://whatsapp-meta-ph-wzewk.ondigitalocean.app`
5. DO: `META_APP_ID=2053406131958490` + config_id (N4) + App Secret Encrypted.
6. Codigo: `app/hub/routes.py` + `app/config.py`.

**Seguranca:** App Secret em print/chat → preferir Reset no Meta e atualizar so o DO. Nunca no Git/agente/C++.

---

## Onde encontrar `DATABASE_URL` e `HUB_PULL_SECRET` (N1 / DO)

### DigitalOcean (evidencia print 22/09/2026)

1. Apps → `whatsapp-meta-ph` → Settings → Environment Variables.
2. `DATABASE_URL` = `${dev-db-085123.DATABASE_URL}` (**ja correto**).
3. `HUB_PULL_SECRET` estava **vazio** → colar o valor do `.env` local do agente.
4. Checklist: `docs/CHECKLIST_HUB_DIGITALOCEAN.md`.
5. Aplicar SQL `001`+`002` no Postgres `dev-db-085123` → Redeploy → `/health` com `db_ok:true`.

### Agente local

```env
HUB_BASE_URL=https://whatsapp-meta-ph-wzewk.ondigitalocean.app
HUB_PULL_SECRET=<igual ao DO>
META_APP_ID=2053406131958490
DATABASE_URL=postgresql://...@127.0.0.1:12345/whatsapp_ph
```

---

## Ordem obrigatória (não pular)

```text
N1  Deploy hub DO (status retorno)     ← HUB_PULL_SECRET + SQL DO agora
N2  Validar poll status ponta a ponta
N3  Painel React Vite                   ← FEITO (web/dist)
N4  Embedded Signup + pairing (cliente)
N5  Instalador WHATSPH (Windows)
N6  PHVCL + GEPH                        ← Rebuild PH.bpl
N7  Templates produto + piloto + App Review
```

---

## N1 — Hub DigitalOcean: retorno de status (Meta → DO → agente)

### Por que esta fase agora
A Meta **não** chama `localhost`. Status (sent/delivered/read/failed) chega só no webhook HTTPS do hub. O agente já tem poller; falta o hub em produção com as mesmas variáveis e o schema no Postgres DO.

### N1.1 — Variáveis no App DO (`whatsapp-meta-ph`)

Garantir (Encrypted onde fizer sentido):

| Variável | Obrigatório | Nota |
|----------|-------------|------|
| `APP_ROLE` | **Sim** | `hub` (Procfile já prefixa; confirme no DO) |
| `APP_ENV` | Sim | `production` |
| `LOG_LEVEL` | Sim | `INFO` |
| `META_WEBHOOK_VERIFY_TOKEN` | Sim | Já existe |
| `META_APP_SECRET` | Sim | Já existe — HMAC obrigatório no código atual |
| `DATABASE_URL` | Sim | Postgres gerenciado DO |
| `HUB_PULL_SECRET` | **Sim — novo** | Mesmo valor no `.env` do agente local |
| `GRAPH_API_VERSION` | Recomendado | `v25.0` |
| `META_APP_ID` | Depois (N4) | Embedded Signup |
| `META_EMBEDDED_SIGNUP_CONFIG_ID` | Depois (N4) | Embedded Signup |

**Não** colocar `META_ACCESS_TOKEN` no DO (token de envio fica no agente / pairing).

### N1.2 — Schema no Postgres do DigitalOcean

No banco apontado por `DATABASE_URL` do DO, aplicar **o mesmo** `sql/001_whatsapp_ph.sql` (no mínimo a tabela `whatsapp_webhook_event`).

Checklist:

1. Conectar no Postgres DO (connection string do painel DO).  
2. `\dt` — ver se `whatsapp_webhook_event` existe.  
3. Se não: rodar `001_whatsapp_ph.sql`.  
4. Confirmar: `SELECT COUNT(*) FROM whatsapp_webhook_event;`

### N1.3 — Deploy do `main` atual

1. DigitalOcean App → redeploy a partir do GitHub `danrleinascimento/whatsapp-meta-ph` branch `main`.  
2. Aguardar Healthy.  
3. Testar:  
   `GET https://whatsapp-meta-ph-wzewk.ondigitalocean.app/health`  
   Esperado: `"role":"hub"`, `db_ok: true` (se `DATABASE_URL` ok).

### N1.4 — Webhook Meta (já verificado — revalidar)

Callback continua:  
`https://whatsapp-meta-ph-wzewk.ondigitalocean.app/webhook/whatsapp`

Campos: pelo menos `messages` (statuses vêm nesse campo).

### N1.5 — Agente local: alinhar poll

No `.env` do PC/dev (e depois no cliente):

```env
HUB_BASE_URL=https://whatsapp-meta-ph-wzewk.ondigitalocean.app
HUB_PULL_SECRET=<mesmo_valor_do_DO>
POLL_INTERVAL_SECONDS=10
```

Reiniciar uvicorn agente. Logs devem mostrar poller ativo; sem `waba_id` na config o poll **pula** (regra atual).

### N1.6 — Teste de aceite N1 (obrigatório)

1. Enviar template ou PDF pelo agente (já sabemos que funciona).  
2. Anotar `meta_message_id` (resposta JSON / tabela `whatsapp_message`).  
3. No Postgres **DO**:  
   `SELECT id, waba_id, field_name, received_at FROM whatsapp_webhook_event ORDER BY id DESC LIMIT 10;`  
   Deve aparecer evento após a Meta notificar.  
4. No Postgres **local**:  
   `SELECT id, status, meta_message_id, updated_at FROM whatsapp_message WHERE meta_message_id = '...';`  
   Status deve evoluir: `ACCEPTED` → `SENT` / `DELIVERED` / `READ` (conforme Meta).  
5. Painel (`gen_panel_ticket`) mostra o status novo.

**Aceite N1:** status muda no DB/painel **sem** o escritório configurar webhook.

### N1.7 — Melhorias de código (se o aceite falhar / polish)

Implementar só com evidência de falha:

| # | Tarefa |
|---|--------|
| N1.7a | Persistir `since` do poller em disco/DB (hoje zera ao reiniciar) |
| N1.7b | Idempotência webhook por `wamid`+status (evitar linhas duplicadas) |
| N1.7c | Tabela hub de pairing em Postgres (hoje `_PAIRING` em memória — ok single worker) |
| N1.7d | Log estruturado quando pull retorna 401 (secret errado) |

---

## N2 — Validação ponta a ponta do retorno (checklist operacional)

Repetir N1.6 em dois cenários:

| Cenário | Ação | Esperado |
|---------|------|----------|
| A | Template utility | Status até DELIVERED/READ |
| B | PDF document | Idem |
| C | Número inválido / falha Meta | `FAILED` + `error_code` no local |
| D | Reiniciar agente no meio | Após N1.7a: continua do `since`; sem isso: reprocessa (status idempotente ok) |

Documentar prints/SQL no chat ou em `ajustes` do projeto quando passar.

---

## N3 — Painel WHATSPH (UI moderna) — IMPLEMENTADO

Stack: **FastAPI + React + Vite + Tailwind** em `web/`. Brand WHATSPH / PH Softwares (teal + Sora/IBM Plex). Ticket GEPH obrigatório.

| # | Tarefa | Status |
|---|--------|--------|
| N3.1 | Validar status DELIVERED após N1 | Pendente (depende DO) |
| N3.2 | Scaffold React+Vite+Tailwind `web/` | **Feito** |
| N3.3 | Build `dist/` + agente serve `/` e `/assets` | **Feito** |
| N3.4 | Filtros status + busca | **Feito** |
| N3.5 | Sessão `/v1/panel/session` (conectado / telefone) | **Feito** |
| N3.6 | GEPH abre URL com ticket | Com N6 (`CreatePanelTicket`) |

**Aceite N3:** `python scripts\gen_panel_ticket.py ADMIN` → browser mostra UI React com histórico.

---

## N4 — Embedded Signup + pairing (WhatsApp **do cliente**)

Hoje o envio usa token PH Softwares (dev). Produto exige WABA do escritório.

Fontes: [Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup/) · [Implementation](https://developers.facebook.com/docs/whatsapp/embedded-signup/implementation/).

| # | Tarefa |
|---|--------|
| N4.1 | Meta App: Login for Business + Embedded Signup `config_id` |
| N4.2 | Domínios OAuth / Valid OAuth Redirect = URL do hub DO |
| N4.3 | Env DO: `META_APP_ID`, `META_EMBEDDED_SIGNUP_CONFIG_ID`, `META_APP_SECRET` |
| N4.4 | Página `/onboarding?installation_id=` (scaffold já existe) — completar fluxo sessionInfo |
| N4.5 | `POST /v1/hub/embedded-signup/exchange` — code→token (já scaffold) |
| N4.6 | `POST /{WABA}/subscribed_apps` após signup |
| N4.7 | `POST /{PHONE}/register` se necessário (pular se Coexistence / já registrado) |
| N4.8 | Pairing: `pair_code` → agente `POST /v1/whatsapp/pairing/claim` → token cifrado em `whatsapp_config` |
| N4.9 | Orientar pagamento na WABA **do cliente** |
| N4.10 | Coexistence (opcional): `featureType: whatsapp_business_app_onboarding` + webhooks `history` / `smb_*` — fallback número só Cloud API |
| N4.11 | Iniciar Tech Provider / App Review / Advanced Access (Meta) |

**Aceite N4:** escritório piloto conecta sem ver DigitalOcean; envio usa token **dele**.

---

## N5 — Instalador Windows (`{PHSFTW}\WHATSPH\`)

| # | Tarefa |
|---|--------|
| N5.1 | Inno Setup: pasta PHSFTW |
| N5.2 | Copiar app + `.venv` embed / runtime Python 3.12 |
| N5.3 | Criar DB `whatsapp_ph` + aplicar `sql/001_whatsapp_ph.sql` |
| N5.4 | Gerar `installation_id`, `PH_API_KEY`, `TOKEN_ENCRYPTION_KEY`, `PANEL_TICKET_SECRET`, `HUB_PULL_SECRET` (ou claim no 1º start) |
| N5.5 | `.env` com `APP_ROLE=agent`, `BIND` loopback `8765`, `HUB_BASE_URL` |
| N5.6 | NSSM/WinSW serviço `PHWhatsMeta` — start automático, logs em `WHATSPH\logs\` |
| N5.7 | Atalho “Painel” → só via GEPH ticket (atalho direto = 403, conforme Q-LOGIN) |
| N5.8 | Teste Win10/11 + Server |

**Aceite N5:** técnico sobe serviço; `/health` + `db_ok` sem instalar Python “na mão”.

---

## N6 — PHVCL + GEPH (integração C++ Builder 5)

### Premissas congeladas
- Encoding **CP1252** + CRLF (REGRA_CODIFICACAO GEPH).  
- Fallback: se Meta **não** CONECTADO → Whats.exe atual.  
- Login painel: **só ticket** gerado pelo GEPH (HMAC).  
- PDF: paths sob PHSFTW / DiretorioPrincipal / Secundario.  
- Fora da janela 24h: **template** + PDF (header document quando aplicável).

### N6.1 — Cliente HTTP na PHVCL

| # | Tarefa | Status 22/09/2026 |
|---|--------|-------------------|
| N6.1.1 | Unit `WhatsMetaClient` (Indy): base `http://127.0.0.1:8765` | **Feito** (`WhatsMetaClient.h/.cpp`, CP1252) |
| N6.1.2 | Header `X-PH-Api-Key` (lido de `{root}\WHATSPH\.env`) | **Feito** |
| N6.1.3 | Métodos: Health / status / SendDocument / CreatePanelTicket | **Feito** (SendTemplate/Batch depois) |
| N6.1.4 | Timeout generoso em upload PDF | **Feito** (120s) |
| N6.1.5 | Mapear erros Meta para PT | Parcial (detail JSON) |

### N6.1b — Linker BCB5 (causa do Unresolved external)

Erros `[Linker Error] Unresolved external 'TWhatsMetaClient::...' referenced from SENWA.OBJ` = `SenWA.cpp` chama a classe, mas o `.cpp` **não entrava** no pacote.

Correção aplicada (CP1252 / REGRA_CODIFICACAO):

| Arquivo | Alteração |
|---------|-----------|
| `WhatsMetaClient.h` / `.cpp` | Implementação (já no disco; status SVN **added**) |
| `SenWA.cpp` | `#include` + `enviarViaWhatsMeta` antes do Whats.exe |
| `PH.cpp` | `USEUNIT("WhatsMetaClient.cpp");` antes de `USEFORM("SenWA.cpp"...` |
| `PH.bpk` | `..\bpl\WhatsMetaClient.obj` em `OBJFILES` (antes de `SenWA.obj`) |
| `Preview.cpp` | **Não** alterar (diff SVN era só comentário; mantido base) |

**O que falta no IDE (você):**

1. Fechar o diálogo “Can't load package … PH.bpl” (BPL antigo quebrado).  
2. Abrir pacote `PH.bpk` no C++ Builder 5.  
3. **Project → Build PH** (ou Rebuild).  
4. Confirmar geração de `C:\CBuilder5\Projects\Lib\bpl\WhatsMetaClient.obj` e `PH.bpl`.  
5. Só depois abrir o projeto GEPH / PH.exe que depende do BPL.

Se o IDE não listar `WhatsMetaClient.cpp` no Project Manager: Add to Project → `WhatsMetaClient.cpp` → Rebuild.

### N6.2 — UI / fluxos GEPH

| # | Tarefa | Status |
|---|--------|--------|
| N6.2.1 | Menu: WhatsApp → Status / Conectar / Abrir painel | Pendente |
| N6.2.2 | Conectar: browser hub `/onboarding?installation_id=` | Pendente (N4) |
| N6.2.3 | Abrir painel: `CreatePanelTicket` → `ShellExecute` | Pendente |
| N6.2.4 | Envio relatório: `SenWA` Meta → fallback Whats.exe | **Código feito** — validar após Build |
| N6.2.5 | Boletos / RLBol: lote `send-batch` | Pendente |
| N6.2.6 | Passar usuario/dirs/paths | **Feito** em `SenWA` |
| N6.2.7 | Reusar `PermiteEnviarWhats` | Conferir |
| N6.2.8 | Compilar `PH.bpl` + GEPH | **Fazer no BCB5 agora** |

### N6.3 — Aceite N6

- [ ] `PH.bpl` compila sem Unresolved external `TWhatsMetaClient`  
- [ ] Status CONECTADO no menu  
- [ ] PDF/boleto chega via Meta pelo SenWA/Preview  
- [ ] Desconectado → Whats.exe intacto  
- [ ] Painel abre só com ticket do GEPH  

---

## N7 — Templates de produto, limites, piloto, App Review

| # | Tarefa |
|---|--------|
| N7.1 | Modelo utility “boleto/relatório” (doc para escritório aprovar na WABA dele) |
| N7.2 | Não usar `hello_world` em número comercial (erro 131058) |
| N7.3 | Sempre listar/resolver via `/v1/whatsapp/templates` (já no agente) |
| N7.4 | Mensagens de erro: 132001, 131058, 130497, 131056 (pair rate) |
| N7.5 | Manual usuário: conectar, pagamento, templates |
| N7.6 | Manual técnico: instalador, portas, logs, `HUB_PULL_SECRET` |
| N7.7 | Piloto 1–2 escritórios |
| N7.8 | Verificação empresa Meta + App Review Tech Provider conforme escala |

---

## Critérios de aceite finais (produto v1)

- [ ] Escritório instala WHATSPH sem configurar Meta Developers  
- [ ] Conecta WhatsApp **dele** (Embedded Signup)  
- [ ] Envia relatório/boleto (template + PDF) pelo GEPH  
- [ ] Painel local: histórico + status (retorno via hub)  
- [ ] Dois escritórios isolados (tokens/WABAs distintos)  
- [ ] Fallback Whats.exe se desconectado  
- [ ] App Secret nunca no C++ / pacote cliente  

---

## Plano de implementação sugerido (sprints)

| Sprint | Escopo | Saída |
|--------|--------|-------|
| **S1** | N1 + N2 | Status DELIVERED no painel local via poll DO |
| **S2** | N3 polish mínimo | Filtros/detalhe se necessário |
| **S3** | N4 | Piloto conecta WABA própria |
| **S4** | N5 | Instalador + serviço Windows |
| **S5** | N6 | GEPH envia pelo Preview Meta |
| **S6** | N7 | Template produto + piloto + Review |

---

## Comandos úteis (dev)

```powershell
cd C:\projetos\python\whatsmeta
.\.venv\Scripts\activate

# Agente
uvicorn app.main:app --host 127.0.0.1 --port 8765

# Templates oficiais da WABA
python scripts\list_templates.py

# Envio
python scripts\smoke_test.py --send-template --to 5549XXXXXXXXX

# Painel
python scripts\gen_panel_ticket.py ADMIN
```

Hub local (só se precisar debugar papel hub):

```powershell
$env:APP_ROLE='hub'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## Riscos (não esquecer)

| Risco | Mitigação |
|-------|-----------|
| Postgres DO sem tabela webhook | N1.2 antes de validar poll |
| `HUB_PULL_SECRET` diferente DO vs agente | 401 no poller — alinhar |
| Token no print/chat | Rotacionar System User token |
| `hello_world` em número real | Usar template APPROVED da WABA |
| Pairing em memória no hub | Single worker DO; depois tabela Postgres |
| App Review / Tech Provider | Começar N4.11 cedo |
| Graph v20 EOL | Manter `v25.0` |

---

## Próxima sessão de implementação (imediato)

1. **DO agora (você):**  
   - Adicionar `HUB_PULL_SECRET` = valor do `.env` local  
   - Adicionar `META_APP_ID=2053406131958490`  
   - Aplicar `sql/001` + `sql/002` no Postgres `dev-db-085123`  
   - Redeploy → confirmar `/health` com `db_ok: true`  
2. **N6.1b** — Rebuild `PH.bpl` no C++ Builder 5.  
3. **N1.5–N1.6** — provar status DELIVERED no painel React.  
4. Depois: N4 (`config_id` Embedded Signup) / N5 / restante N6.

**Fim do roteiro de próximos passos.**
