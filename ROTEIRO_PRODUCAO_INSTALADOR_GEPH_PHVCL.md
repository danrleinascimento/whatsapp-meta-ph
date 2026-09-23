# Roteiro completo de produção — Instalador WHATSPH + GEPH + PHVCL

**Documento:** roteiro executável do início ao fim para colocar o WhatsApp Meta Cloud API em produção no escritório (serviço Windows + desktop GEPH).  
**Criado:** 22/09/2026 · **Revisão implementação:** 23/09/2026  
**Versão app:** `0.2.4`  
**Não substitui:** `ROTEIRO_PROXIMOS_PASSOS_WHATSPH.md` nem `ROTEIRO_COMPLETO_DESENVOLVIMENTO_WHATSAPP_META_PH.md`.

---

## Status da implementação (23/09/2026)

| Fase | Conteúdo | Status código | O que falta (manual) |
|------|----------|---------------|----------------------|
| A | Hub schema persistente | migrate + memory OK; hub **0.2.4** | Neon/doadmin → `schema_ok=true` |
| B | Build PH.bpl + GEPH | fontes + bpk OK; **Ui.obj ausente** | **Rebuild PH.bpl + GEPH no BCB5** |
| C | Telas Status / Painel | `WhatsMetaUi` + botões Preview | Validar no exe após Build |
| D | `dist\whatsph` | pasta gerada com `.venv` | Copiar **`nssm.exe`** |
| E | Inno + NSSM | `.iss` 0.2.4 + bats | Instalar Inno 6 + Compile Setup |
| F | Teste VM / aceite | checklist no roteiro | Rodar Setup + health |
| G | Embedded Signup | scaffold hub | `config_id` Meta |
| H | Piloto | docs | após F+G |

### Artefatos novos (23/09)

| Path | Função |
|------|--------|
| `scripts/build_dist.ps1` | Gera `dist\whatsph` (app+venv+web+sql+bats) |
| `installer/first_run.py` + `.bat` | Gera `.env` inicial |
| `installer/apply_sql.bat` | Aplica SQL no Postgres local |
| `installer/install_service.bat` | NSSM + logs |
| `installer/WHATSPH.iss` | Setup `WHATSPH_Setup_0.2.4.exe` |
| `installer/README_INSTALACAO.txt` | Manual curto |
| `phvcl/WhatsMetaUi.h/.cpp` | Status + Abrir painel |
| `phvcl/WhatsMetaClient` | +`FetchStatus` +`InstallationId` |
| `Preview.cpp` | Botões **Meta** / **Painel** ao lado do Whats |

---

## Regras absolutas (ler antes de qualquer edição)

| # | Regra |
|---|--------|
| 1 | Só API oficial Meta Cloud API / Graph. |
| 2 | `META_APP_SECRET` **somente** no hub DigitalOcean. Nunca no instalador, `.env` do agente de cliente, C++, ou Git. |
| 3 | Fontes `.cpp` / `.h` / `.dfm` = **CP1252 + CRLF** (`REGRA_CODIFICACAO.md` no GEPH). Não salvar UTF-8. |
| 4 | Agente escuta só **loopback** `127.0.0.1:8765`. |
| 5 | Painel web: **somente** com ticket HMAC gerado pelo GEPH/API (`POST /v1/panel/ticket`). URL sem ticket = bloqueio. |
| 6 | Se agente offline ou WhatsApp não `CONNECTED` → manter fluxo legado **Whats.exe** (SenWA já faz fallback). |
| 7 | Telefone Meta no SenWA: **11 dígitos** (DDD+número); envio Graph usa `55` + esses dígitos. |

---

## 0. O que já está pronto (verificado 23/09/2026 08:45)

| Camada | Evidência |
|--------|-----------|
| Hub DO | `/health` → `role=hub` **`v0.2.4`** `db_ok=true` `schema_ok=false` `events_backend=memory` |
| GitHub | `main` @ `8fa1ca1` |
| `dist\whatsph` | Existe: app, `.venv`, `web\dist`, sql, bats — **falta `nssm.exe`** |
| Instalador scripts | `first_run` / `apply_sql` / `install_service` / `WHATSPH.iss` 0.2.4 |
| Inno Setup neste PC | **Não instalado** (ISCC.exe ausente) |
| PHVCL fontes | Client + Ui + SenWA + Preview + PH.cpp/bpk — **CP1252 OK** |
| `WhatsMetaClient.obj` | Existe |
| `WhatsMetaUi.obj` | **NÃO existe** → Rebuild PH.bpl **obrigatório** |
| Agente `:8765` agora | **Offline** (subir quando for testar) |
| Painel React / smoke Meta | Já comprovados em 22/09 |
| Embedded Signup `config_id` | Ainda não criado |

**Caminhos fixos**

| Item | Path |
|------|------|
| Código Python | `C:\projetos\python\whatsmeta` |
| GitHub | `https://github.com/danrleinascimento/whatsapp-meta-ph` |
| Hub | `https://whatsapp-meta-ph-wzewk.ondigitalocean.app` |
| PHVCL | `C:\CBuilder5\Projects\Lib\phvcl` |
| BPL saída | `C:\CBuilder5\Projects\Lib\bpl\PH.bpl` |
| GEPH | `C:\CBuilder5\Projects\GEPH` |
| Runtime cliente | `{PHSFTW}\WHATSPH\` (ex. `C:\PHSFTW\WHATSPH`) |
| Meta App ID | `2053406131958490` |

---

## 1. Arquitetura em produção (referência)

```text
[GEPH / PH.exe]
    |  Indy HTTP + header X-PH-Api-Key
    v
[Serviço Windows PHWhatsMeta]  ← instalador
    127.0.0.1:8765  APP_ROLE=agent
    Postgres local whatsapp_ph
    Painel React em web/dist (ticket)
    |  poll HUB_PULL_SECRET
    v
[Hub DigitalOcean]  APP_ROLE=hub
    webhook Meta HTTPS
    (ideal: Postgres com schema_ok=true)
    |
    v
[Meta Graph API v25.0]
```

### Contrato HTTP que o GEPH/PHVCL usa (já implementado no agente)

| Método | Path | Auth | Uso desktop |
|--------|------|------|-------------|
| GET | `/health` | — | Diagnóstico |
| GET | `/v1/whatsapp/status` | `X-PH-Api-Key` | Menu Status / `IsConnected` |
| POST | `/v1/whatsapp/send-document` | API key | SenWA PDF |
| POST | `/v1/whatsapp/send-template` | API key | (futuro UI / lote) |
| POST | `/v1/whatsapp/send-batch` | API key | Boletos grupo |
| POST | `/v1/panel/ticket` | API key | Abrir painel no browser |
| GET | `/v1/panel/session?ticket=` | ticket | SPA React |
| GET | `/v1/panel/messages?ticket=` | ticket | SPA React |
| POST | `/v1/whatsapp/pairing/claim?pair_code=` | API key | Após Embedded Signup (N4) |

### Métodos já existentes em `TWhatsMetaClient`

| Método | Chama |
|--------|--------|
| `LoadFromWhatsPhEnv(root)` | Lê `{root}\WHATSPH\.env` → `PH_API_KEY`, `PORT` |
| `HealthOk()` | `GET /health` |
| `IsConnected()` | `GET /v1/whatsapp/status` → `connected` |
| `SendDocument(...)` | `POST /v1/whatsapp/send-document` |
| `CreatePanelTicket(user, url)` | `POST /v1/panel/ticket` |

**Ainda não existem no C++ (criar só se a tela precisar):** `SendTemplate`, `SendBatch`, `ClaimPairing` — o agente já tem as rotas.

---

## 2. Ordem obrigatória das fases

```text
Fase A  Hub persistente (Neon/doadmin)     — antes de piloto externo
Fase B  Build PH.bpl + GEPH                — desktop linka
Fase C  Telas / menus GEPH + chamadas      — UX produção
Fase D  Empacotar dist\whatsph             — artefato do instalador
Fase E  Inno Setup + NSSM + SQL            — .exe
Fase F  Teste VM / aceite instalador
Fase G  Embedded Signup (N4)               — WABA do cliente
Fase H  Piloto + manuais + App Review
```

Não inverter: **sem B+C funcionando no PC de dev**, o instalador (E) só empacota algo incompleto.  
Sem A, status DELIVERED pode falhar após redeploy do hub (memória).

---

# FASE A — Hub com schema persistente

**Por quê:** Dev Database DO (`whatsapp-meta-db`) conecta (`db_ok=true`) mas **não permite CREATE** em `public` → `schema_ok=false` → eventos em memória.

### A.1 Escolher um caminho

| Opção | Ação |
|-------|------|
| **A1 Neon** (rápido) | Criar projeto Neon → copiar connection string (usuário dono) |
| **A2 doadmin** | Obter senha `doadmin` do cluster → `scripts/apply_sql_doadmin.py` |
| **A3 Managed PG** | Postgres Managed em região DO que suporte (ex. NYC) e anexar ao App |

### A.2 No DigitalOcean App `whatsapp-meta-ph`

1. Settings → Web Service → Environment Variables  
2. `DATABASE_URL` = connection string nova **ou** binding Managed (não voltar a `dev-db-085123`)  
3. Manter: `HUB_PULL_SECRET`, `META_APP_SECRET`, `META_WEBHOOK_VERIFY_TOKEN`, `APP_ENV=production`  
4. Adicionar se faltar: `META_APP_ID=2053406131958490`, `GRAPH_API_VERSION=v25.0`  
5. Save → aguardar Healthy  

### A.3 Schema

- Automático no startup do hub (`migrate` aplica `sql/001` + `002`), **ou**  
- Manual: `POST /v1/hub/migrate` com header `X-PH-Hub-Secret`

### A.4 Aceite A

```text
GET .../health
→ "schema_ok": true
→ "events_backend": "postgres"   (campo some ou deixa de ser memory)
```

Enviar template pelo agente → status no painel chega a **DELIVERED** (N2).

---

# FASE B — Build PHVCL + GEPH

### B.1 Arquivos PHVCL (já no disco)

| Arquivo | Obrigatório |
|---------|-------------|
| `WhatsMetaClient.h` | Sim |
| `WhatsMetaClient.cpp` | Sim |
| `SenWA.cpp` (include + `enviarViaWhatsMeta`) | Sim |
| `PH.cpp` `USEUNIT("WhatsMetaClient.cpp")` | Sim |
| `PH.bpk` `WhatsMetaClient.obj` | Sim |
| `Preview.cpp` | **Não alterar** para WhatsMeta (já chama SenWA) |

### B.2 Passos no C++ Builder 5

1. Fechar diálogo “Can't load package PH.bpl” se aparecer.  
2. Abrir `C:\CBuilder5\Projects\Lib\phvcl\PH.bpk`.  
3. Project Manager: confirmar `WhatsMetaClient.cpp`. Se ausente: **Add to Project**.  
4. **Project → Build PH** (ou Rebuild).  
5. Confirmar:
   - `C:\CBuilder5\Projects\Lib\bpl\WhatsMetaClient.obj`
   - `C:\CBuilder5\Projects\Lib\bpl\PH.bpl`
6. Zero erros `Unresolved external 'TWhatsMetaClient::...'`.  
7. Abrir projeto **GEPH** → Rebuild do executável que usa `PH.bpl`.  

### B.3 Encoding

- Barra de status / TortoiseMerge: fontes em Windows-1252.  
- Se corromper acentos: `svn revert` + reaplicar só o patch necessário via script CP1252.

### B.4 Aceite B

- [ ] PH.bpl e GEPH compilam  
- [ ] Com agente CONECTADO, SenWA envia PDF via Meta  
- [ ] Com agente parado, SenWA cai no Whats.exe  

### B.5 SVN (quando estável)

Commit: `WhatsMetaClient.*`, `SenWA.cpp`, `PH.cpp`, `PH.bpk` (e depois forms/menus da Fase C).

---

# FASE C — Telas e chamadas no GEPH / PHVCL

## C.0 Premissas de UI

- Não inventar segundo fluxo de envio de relatório: **Preview → `TSendWA1` (SenWA)** já é o caminho; Meta já está no `btnEnviarClick`.  
- Novas telas/menus: Status, Abrir painel, Conectar (N4).  
- Respeitar `vg.usuarioPodeEnviarWhats` / `vg.exigirNumeroParaEnviarWhats` (`DMUsuarios1` / `PermiteEnviarWhats`).

## C.1 Menu principal GEPH — itens a criar

Localizar o menu onde já existe ação WhatsApp (Preview / NavWhats) e adicionar submenu, por exemplo:

```text
WhatsApp
  ├─ Status da conexão...     → Form ou MessageBox com status
  ├─ Abrir painel WHATSPH...  → ticket + ShellExecute
  ├─ Conectar WhatsApp...     → browser hub /onboarding (Fase G)
  └─ (envio de relatório continua pelo Preview → SenWA)
```

Nomes exatos do menu: seguir padrão visual do GEPH existente (não inventar branding paralelo).

## C.2 Tela / ação “Status da conexão”

### Comportamento

1. `TWhatsMetaClient Cli;`  
2. `Cli.LoadFromWhatsPhEnv(vg.DiretorioPrincipal)` — se falhar, tentar `C:\PHSFTW`.  
3. Se `!Cli.HealthOk()` → mensagem: agente offline / serviço parado.  
4. Se `Cli.IsConnected()` → “Conectado” + (opcional) telefone via JSON já lido em `IsConnected`/status.  
5. Senão → “Desconectado — use Conectar ou contate suporte”.  

### Implementação sugerida (mínima)

- Sem form novo: `ShowMensagem` / `MessageDlg` com texto montado.  
- Ou form simples PHVCL `FrmWhatsMetaStatus` (1 label + botão Atualizar + Fechar) se o padrão do sistema exigir form.

### Chamada serviço

`GET /v1/whatsapp/status` com `X-PH-Api-Key` (já em `IsConnected` / pode estender client para devolver `display_phone`).

**Gap atual:** `IsConnected()` só retorna bool. Na Fase C.2b (opcional): adicionar em `WhatsMetaClient` método `GetStatus(AnsiString &OutJson)` ou campos `DisplayPhone`, `StatusText` preenchidos no mesmo GET — **CP1252**.

## C.3 Ação “Abrir painel WHATSPH”

### Comportamento

1. Carregar env / API key (igual Status).  
2. `Cli.CreatePanelTicket(vg.NomeUsuario, Url)`.  
3. Se ok: `ShellExecute(0, "open", Url.c_str(), NULL, NULL, SW_SHOWNORMAL)`.  
4. Se falha: mostrar `Cli.LastError`.  

### Chamada serviço

`POST /v1/panel/ticket` body JSON `{"usuario_geph":"..."}` → `panel_url`.

### Já existe no C++

`TWhatsMetaClient::CreatePanelTicket` — só falta **ligar ao menu**.

## C.4 Ação “Conectar WhatsApp” (depende Fase G)

1. Montar URL:  
   `https://whatsapp-meta-ph-wzewk.ondigitalocean.app/onboarding?installation_id=<INSTALLATION_ID>`  
   (`INSTALLATION_ID` lido do `.env` WHATSPH — pode exigir novo método `LoadInstallationId` no client).  
2. `ShellExecute` no browser.  
3. Após signup, usuário informa `pair_code` **ou** tela pede o código → `POST /v1/whatsapp/pairing/claim`.  

**Antes da Fase G:** item de menu desabilitado ou mensagem “Em configuração”.

## C.5 Envio de relatório (já feito — só validar)

Fluxo real:

```text
Preview (botão WhatsApp)
  → new TSendWA1
  → btnEnviarClick
      → enviarViaWhatsMeta(...)   // Meta
      → se falhar: FTP + Whats.exe // legado
```

### Checklist teste C.5

- [ ] Usuário com `PermiteEnviarWhats`  
- [ ] Telefone 11 dígitos  
- [ ] PDF sob pasta permitida (PHSFTW / DiretorioPrincipal / Secundario)  
- [ ] Agente CONECTADO → mensagem no celular + linha no painel  
- [ ] Agente parado → Whats.exe  

## C.6 Lote de boletos (depois do aceite C.5)

Hoje: `Preview` → `enviarWhatsGrupoBoletos` / `NavWhats` (legado).  

Produção Meta:

1. Estender `WhatsMetaClient` com `SendBatch` **ou** loop `SendDocument` com pacing (agente já tem `PAIR_RATE` / `send-batch`).  
2. Preferir `POST /v1/whatsapp/send-batch` (agente já implementa).  
3. Manter limite de quantidade do Preview (`recusarWhatsGrupoPorLimite`).  
4. Fora da janela 24h: template utility + documento (N7).

**Ordem:** só após C.5 aceito.

## C.7 Onde colocar código (decisão de pacote)

| Peça | Pacote |
|------|--------|
| `WhatsMetaClient` | PHVCL (`PH.bpl`) — **já** |
| Hook SenWA | PHVCL — **já** |
| Menu Status / Painel / Conectar | Preferir **PHVCL** se o menu do Preview/principal estiver na PHVCL; senão form no **GEPH** que chama PHVCL |
| ShellExecute | `ShellApi.h` (padrão Windows) |

Antes de criar form no GEPH: inspecionar no BCB5 onde está o menu do Preview WhatsApp (unit real) — **não adivinhar nome do form**; abrir Project Manager do GEPH e localizar.

## C.8 Aceite Fase C

- [ ] Menu Status reflete agente  
- [ ] Menu Abrir painel abre React com ticket  
- [ ] SenWA Meta validado em build de produção  
- [ ] Sem App Secret no binário (strings: só `127.0.0.1`, paths WHATSPH)  

---

# FASE D — Empacotar `dist\whatsph` (conteúdo do instalador)

### D.1 Pré-requisitos no PC de build

- Python 3.12  
- Node.js (build do painel)  
- Repo `whatsmeta` atualizado (`main`)  

### D.2 Build frontend

```powershell
cd C:\projetos\python\whatsmeta\web
npm ci
npm run build
# gera web\dist\
```

### D.3 Criar árvore de distribuição

```text
dist\whatsph\
  app\                 (pacote Python completo)
  web\dist\            (painel)
  sql\001_whatsapp_ph.sql
  sql\002_whatsapp_pairing.sql
  sql\003_whatsapp_poll_state.sql
  scripts\apply_sql.py
  scripts\seed_dev_config.py   (NÃO no cliente final; só lab)
  requirements.txt
  .venv\               (ou python embed — ver D.4)
  nssm\nssm.exe
  install_service.bat
  apply_sql.bat          (criar)
  first_run.bat          (criar — gera .env)
  README_INSTALACAO.txt
```

**Não incluir:** `.env` com secrets de lab, `META_ACCESS_TOKEN`, App Secret, `.git`.

### D.4 Runtime Python no cliente (escolher uma)

| Opção | Prós | Contras |
|-------|------|---------|
| **D4a** `.venv` copiado do build Win** mesmo arch** | Simples | Pacote grande; paths |
| **D4b** Embeddable Python 3.12 + `pip install -r requirements.txt` no Setup | Mais limpo | Script de post-install |
| **D4c** PyInstaller one-folder | Um exe | Mais trabalho de packaging |

**Recomendação v1:** D4a ou D4b. O `install_service.bat` atual assume:

`{app}\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765`

### D.5 Scripts a criar (ainda não existem todos)

#### `apply_sql.bat`

```bat
@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" scripts\apply_sql.py
if errorlevel 1 exit /b 1
```

(Precisa `DATABASE_URL` no ambiente ou `.env` já gerado.)

#### `first_run.bat` / gerador de `.env`

Gerar e gravar em `{app}\.env`:

| Variável | Origem |
|----------|--------|
| `APP_ROLE` | `agent` |
| `APP_ENV` | `production` |
| `BIND_HOST` | `127.0.0.1` |
| `PORT` | `8765` |
| `INSTALLATION_ID` | UUID novo |
| `PH_API_KEY` | `secrets.token_urlsafe(32)` |
| `TOKEN_ENCRYPTION_KEY` | key urlsafe |
| `PANEL_TICKET_SECRET` | urlsafe |
| `HUB_BASE_URL` | `https://whatsapp-meta-ph-wzewk.ondigitalocean.app` |
| `HUB_PULL_SECRET` | valor de fábrica PH (**igual ao DO**) |
| `GRAPH_API_VERSION` | `v25.0` |
| `PHSFTW_ROOT` | pasta pai do WHATSPH |
| `DATABASE_URL` | perguntar ou detectar Postgres do escritório |

### D.6 Aceite D

- Pasta `dist\whatsph` roda **sem** o repo fonte:  
  `cd dist\whatsph` → `.\.venv\Scripts\python.exe -m uvicorn ...` → `/health` ok.

---

# FASE E — Inno Setup + serviço Windows

### E.1 Arquivos

| Arquivo | Status |
|---------|--------|
| `installer/WHATSPH.iss` | Rascunho — versionar `0.2.3`, Source = `dist\whatsph\*` |
| `installer/install_service.bat` | Existe — usa NSSM `PHWhatsMeta` |
| `apply_sql.bat` / `first_run.bat` | **Criar** (Fase D) |

### E.2 Ajustes no `.iss`

1. `#define MyAppVersion "0.2.3"`  
2. `DefaultDirName={code:GetPhsftw}\WHATSPH` (já tenta `C:\PHSFTW` / `D:\PHSFTW`)  
3. `[Files]` → `Source: "..\dist\whatsph\*"`  
4. `[Run]` ordem:
   1. `first_run.bat` (gera `.env` se não existir)  
   2. `apply_sql.bat`  
   3. `install_service.bat`  
5. Não criar atalho que abra `http://127.0.0.1:8765/` sem ticket.  

### E.3 NSSM (`install_service.bat`)

Já faz:

- `nssm install PHWhatsMeta ... python -m uvicorn app.main:app --host 127.0.0.1 --port 8765`  
- `AppDirectory` = pasta WHATSPH  
- `AppEnvironmentExtra APP_ROLE=agent`  
- `SERVICE_AUTO_START`  

Completar na implementação:

- Log stdout/stderr → `WHATSPH\logs\service.log` (`AppStdout` / `AppStderr`)  
- Dependência: se Postgres for serviço Windows, opcional `DependOnService`  

### E.4 Compilar

1. Abrir Inno Setup 6 → Compile `WHATSPH.iss`  
2. Saída: `WHATSPH_Setup_0.2.3.exe`  

### E.5 Aceite E

- [ ] Setup compila sem erro  
- [ ] Instalação admin conclui  
- [ ] Serviço `PHWhatsMeta` = Running  

---

# FASE F — Teste de aceite do instalador (VM)

### F.1 Ambiente

- Windows 10/11 limpo (ou Server)  
- Postgres acessível (instalar ou usar o do PH)  
- Porta 8765 livre  

### F.2 Roteiro de teste

1. Instalar `WHATSPH_Setup_0.2.3.exe`  
2. Verificar pasta `{PHSFTW}\WHATSPH\.env` (sem secrets Meta de envio embutidos de lab)  
3. `services.msc` → `PHWhatsMeta` Running  
4. Browser: `http://127.0.0.1:8765/health` → `role=agent` `db_ok=true`  
5. `http://127.0.0.1:8765/` sem ticket → bloqueado  
6. Com `PH_API_KEY` do `.env`:  
   `POST /v1/panel/ticket` → abrir `panel_url` → React ok  
7. Seed/pairing CONECTADO → smoke template  
8. GEPH instalado apontando mesmo PHSFTW → SenWA Meta  

### F.3 Aceite F

- [ ] Itens F.2 todos OK  
- [ ] Desinstalar/reinstalar não quebra (ou documentar backup `.env`)  

---

# FASE G — Embedded Signup (WABA do cliente)

Só após F estável.

| # | Tarefa |
|---|--------|
| G.1 | Meta: Login for Business + Embedded Signup → `config_id` |
| G.2 | OAuth redirect = URL hub DO |
| G.3 | DO env: `META_APP_ID`, `META_EMBEDDED_SIGNUP_CONFIG_ID` |
| G.4 | Completar `/onboarding` + exchange code→token |
| G.5 | Menu GEPH Conectar → browser + claim `pair_code` |
| G.6 | Remover dependência de seed System User PH no cliente |

Aceite: escritório envia com **token dele**.

---

# FASE H — Piloto e operação

| # | Tarefa |
|---|--------|
| H.1 | Template utility “relatório/boleto” na WABA do cliente |
| H.2 | Manual usuário (conectar, painel, envio) |
| H.3 | Manual técnico (serviço, logs, portas, `HUB_PULL_SECRET`) |
| H.4 | Piloto 1–2 escritórios |
| H.5 | App Review / Tech Provider conforme escala |

---

## Matriz “quem implementa o quê”

| Entrega | Onde | Encoding / tool |
|---------|------|-----------------|
| Migrate hub / Neon | `whatsmeta` + DO | UTF-8 |
| Painel React | `web/` | UTF-8 |
| Instalador / bat / iss | `installer/` + `dist/` | UTF-8 / bat OEM ok |
| WhatsMetaClient / SenWA / menus | PHVCL (± GEPH forms) | **CP1252** BCB5 ou script |
| Rebuild GEPH | GEPH `.bpr` | BCB5 |

---

## Sequência sugerida de sprints (execução)

| Sprint | Fases | Saída |
|--------|-------|-------|
| **P1** | B + C.3 + C.5 | GEPH compila; SenWA Meta; Abrir painel |
| **P2** | C.2 + D + E | Status menu; Setup `.exe` |
| **P3** | F | Aceite VM |
| **P4** | A + fechar N2 DELIVERED | Hub `schema_ok` |
| **P5** | C.6 + G | Lote + Embedded Signup |
| **P6** | H | Piloto |

---

## Critérios de aceite finais (produto v1)

- [ ] Escritório instala WHATSPH sem instalar Python manualmente  
- [ ] Serviço `PHWhatsMeta` sobe sozinho no boot  
- [ ] GEPH: Status / Abrir painel / Envio relatório Meta  
- [ ] Fallback Whats.exe se desconectado  
- [ ] Painel só com ticket  
- [ ] Status de mensagem atualiza via hub (ideal `schema_ok=true`)  
- [ ] Cliente conecta WABA própria (G)  
- [ ] App Secret nunca no pacote cliente / C++  

---

## Referências cruzadas

| Doc | Uso |
|-----|-----|
| `ROTEIRO_PROXIMOS_PASSOS_WHATSPH.md` | Estado N1–N7 atual |
| `docs/CHECKLIST_HUB_DIGITALOCEAN.md` | Ops DO |
| `docs/INTEGRACAO_PHVCL_WHATSMETA.md` | Arquivos PHVCL |
| `REGRA_CODIFICACAO.md` (GEPH) | CP1252 |
| `installer/WHATSPH.iss` | Inno |
| `installer/install_service.bat` | NSSM |
| `sql/001_*.sql` … `003_*.sql` | Schema |

---

## Próxima sessão de implementação (começar aqui)

1. **Fase B** — Rebuild `PH.bpl` + GEPH no BCB5 (validar zero Unresolved).  
2. **Fase C.5** — teste SenWA Meta no exe.  
3. **Fase C.3** — menu/botão Abrir painel (`CreatePanelTicket` + `ShellExecute`).  
4. Em paralelo: **Fase D** montar `dist\whatsph` + completar bats.  
5. **Fase E** compilar Setup.  
6. **Fase A** quando for fechar DELIVERED persistente / piloto.

**Fim do roteiro completo de produção.**  
Arquivo: `C:\projetos\python\whatsmeta\ROTEIRO_PRODUCAO_INSTALADOR_GEPH_PHVCL.md`
