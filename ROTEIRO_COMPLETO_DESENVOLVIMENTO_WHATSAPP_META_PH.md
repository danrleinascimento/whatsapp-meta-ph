# Roteiro Completo de Desenvolvimento — WhatsApp Meta Cloud API (PH Softwares)

**Data:** 22/09/2026  
**Documento mestre:** do início ao fim (produto para escritórios)  
**Código:** `C:\projetos\python\whatsmeta` · GitHub `danrleinascimento/whatsapp-meta-ph`  
**PHVCL:** `C:\CBuilder5\Projects\Lib\phvcl` (fase posterior)  
**Primeiro sistema:** GEPH → depois demais via PHVCL Preview  

> **Regra absoluta:** só APIs oficiais Meta (Cloud API + Embedded Signup + Business Management). Proibido WhatsApp Web / Selenium / Baileys / Multidevice não oficial.  
> **Regra absoluta:** App Secret e exchange `code→token` **somente** no hub HTTPS (DigitalOcean). Nunca no C++ / pacote do cliente.  
> Revalidar endpoints na doc Meta no momento de cada fase.

### Fontes oficiais (base deste roteiro)

- [Tech Provider / Partners](https://developers.facebook.com/docs/whatsapp/solution-providers/)  
- [Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup/)  
- [Embedded Signup — implementação](https://developers.facebook.com/docs/whatsapp/embedded-signup/implementation/)  
- [Onboarding pós-signup (register + subscribed_apps)](https://developers.facebook.com/docs/whatsapp/embedded-signup/)  
- [Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/)  
- [Send messages / janela 24h](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages/)  
- [Templates](https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates/)  
- [Media / PDF](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media/)  
- [Document messages](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/document-messages/)  
- [Subscribed Apps API](https://developers.facebook.com/documentation/business-messaging/whatsapp/reference/whatsapp-business-account/subscribed-apps-api)  
- [Graph API changelog](https://developers.facebook.com/docs/graph-api/changelog/) (v26.0 atual; **v20.0** encerra 24/09/2026)  
- [NSSM](https://nssm.cc/) (serviço Windows)

Documentos irmãos (detalhe):  
`ROTEIRO_IMPLEMENTACAO_META_CLOUD_API.md` · `ROTEIRO_AGENTE_LOCAL_WHATSAPP_PH.md`

---

## 1. Objetivo do produto

Cada **escritório** (cliente PH):

1. Instala o pacote WHATSPH no servidor (`PHSFTW`).  
2. No GEPH (e depois outros sistemas), conecta **o WhatsApp dele** (não o da PH).  
3. Envia relatórios/boletos: texto + PDF; lista de destinatários.  
4. Consulta histórico num **painel web local** (quem enviou, para quem, status, máquina, PDF).  
5. Paga a Meta na WABA **dele** (modelo **Tech Provider**).

A PH fornece: App Meta, hub nuvem, agente local, painel, instalador, integração PHVCL.

---

## 2. Arquitetura alvo (três peças)

```text
┌──────────────────────────── ESCRITÓRIO (PHSFTW) ────────────────────────────┐
│  GEPH / EFPH / …  →  PH.bpl (Preview, boletos, menu WhatsApp)                 │
│         │ HTTP 127.0.0.1:8765 + X-PH-Api-Key                                  │
│         │ abre browser → painel / Embedded Signup                             │
│         ▼                                                                     │
│  {PHSFTW}\WHATSPH\   Windows Service (FastAPI + React build)                  │
│         ├── envio Graph (token do escritório, cifrado)                        │
│         ├── poll de eventos no Hub                                            │
│         └── Postgres local whatsapp_ph                                        │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ HTTPS (pairing + pull eventos)
                                        ▼
┌──────────────────────────── HUB PH (DigitalOcean) ──────────────────────────┐
│  App whatsapp-meta-ph                                                         │
│  • GET/POST /webhook/whatsapp  (Meta → todos os WABAs do App PH)              │
│  • Embedded Signup (JS SDK) + exchange code→business token                    │
│  • POST /{WABA}/subscribed_apps · register phone (se aplicável)               │
│  • Fila/eventos por installation_id / waba_id                                 │
│  • App Secret só aqui                                                         │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                        ▼
                                   Meta Graph API
```

**Cliente NÃO configura DigitalOcean.** Webhook é único, da PH, já cadastrado no App Meta.

---

## 3. Decisões congeladas (evidência + alinhamento PH)

| ID | Decisão |
|----|---------|
| Billing | Tech Provider — escritório paga Meta |
| Envio | Agente local (máquina do escritório) |
| Webhook | Hub DigitalOcean único |
| Onboarding cliente | Embedded Signup (browser) no hub PH |
| Painel | `{PHSFTW}\WHATSPH\` — FastAPI + React (Vite) |
| Serviço Windows | Um service (NSSM/WinSW) |
| Porta | `8765` em `127.0.0.1` |
| PDF | Upload `media` → `document.id` |
| Graph API | **`v25.0`** (não usar v20 após 24/09/2026) |
| Postgres cliente | Cluster PHSFTW, DB `whatsapp_ph`, PG **9.5** neste ambiente de dev |
| Retorno status | Hub persiste webhook → agente **poll** → atualiza DB local |
| Coexistência Whats.exe | Se Meta CONECTADO → Cloud API; senão → Whats.exe (PHVCL) |
| Encoding C++ | CP1252 + CRLF (REGRA_CODIFICACAO GEPH) |

### Decisões das respostas PH (22/09/2026) + evidência

| ID | Resposta PH | Decisão técnica |
|----|-------------|-----------------|
| **Q-LOGIN** | Painel usa usuário/senha dos sistemas PH (`DMUsuarios` / `CPUsuarios`); GEPH pode abrir com login automático | Ver §3.1 — **não** reimplementar senha no Postgres do WhatsApp |
| **Q-HIST** | Cada escritório só vê dados **do seu** escritório | Isolamento por instalação (DB/serviço na máquina do escritório). **Dentro** do mesmo escritório: todos os usuários PH veem o histórico do escritório (filtro por usuário = opcional na UI), salvo nova decisão. |
| **Q-COEX** | Coexistence se der para funcionar | **Sim, planejar** via Embedded Signup `featureType: whatsapp_business_app_onboarding` ([doc oficial](https://developers.facebook.com/docs/whatsapp/embedded-signup/custom-flows/onboarding-business-app-users/)); exige Tech Provider + Advanced Access + webhooks extras (`history`, `smb_*`) |
| **Q-TPL** | Lote tipo CPBoletos/RLBol se Meta permitir | **Sim**: template utility + fila com pacing. Meta: até ~80 msg/s por número (default); **1 msg / 6 s por mesmo destinatário** (erro 131056); coexistência fixa ~20 mps ([Throughput](https://developers.facebook.com/docs/whatsapp/cloud-api/overview/)) |
| **Q-DB** | `whatsapp_ph` ≠ `biph` (projetos distintos) | **Sem FK / sem dados cruzados**. São DBs diferentes; o agente só usa `whatsapp_ph`. **Q-DB2:** no pgAdmin, você abre `whatsapp_ph` com qual login (ex. `postgres`)? Precisamos montar `DATABASE_URL` sem misturar com tabelas do `biph`. |

#### 3.1 Login do painel — evidência PHVCL (não inventar)

Cadastro de usuários PH **não** está no Postgres `biph`. Evidência em `DMUsuarios1.h`:

- Arquivos Paradox: `SENUSU.PD` / `SENUDET.PD` (`ARQUIVO_USUARIOS`)
- Caminho via `getCaminhoCadastroUsuarios()` sob pasta PHSFTW / `vg.DiretorioPrincipal`

**Implicação:** o serviço Python **não** deve “adivinhar” o formato/criptografia de `SENUSU.PD` sem especificação. Formas corretas:

| Fluxo | Como fazer (seguro) |
|-------|---------------------|
| **A — GEPH já logado** (preferido) | GEPH gera **ticket de uso único** (HMAC, TTL curto: usuário, código, expira) e abre `http://127.0.0.1:8765/?ticket=...`. WHATSPH valida o ticket com chave local compartilhada no `.env`. **Não** manda senha na URL. |
| **B — Abertura manual do painel** | Tela pede usuário/senha PH. Validação: **(B1)** endpoint local no agente que o GEPH/serviço PH já autenticou, ou **(B2)** rotina acordada de leitura de `SENUSU.PD` **somente após** documentar estrutura `SENUSU` / hash da senha no código PHVCL (fase de análise dedicada). |

**Proibido:** enviar senha do GEPH em query string em claro.

**Pergunta residual Q-LOGIN-B:** **FECHADA (22/09/2026)** — só fluxo A (ticket do GEPH). Abertura manual do painel **deve falhar** (não pede senha; retorna erro / página “abra pelo sistema PH”).

#### 3.2 Lote / templates (Q-TPL) — o que a Meta permite

- Fora da janela 24h: **obrigatório template** aprovado (utility) + PDF no header document quando for o caso.  
- Em massa (RLBol): fila no agente; delay entre envios; respeitar pair-rate (mesmo número a cada ≥6s).  
- Com Coexistence: throughput menor (~20 mps) — fila ainda mais conservadora.  
- Cada WABA do escritório precisa ter o template aprovado (ou clonar modelo PH).

#### 3.3 Coexistence (Q-COEX) — requisitos Meta

- Tech Provider (ou Solution Partner)  
- Embedded Signup + `featureType: whatsapp_business_app_onboarding`  
- WhatsApp Business App ≥ 2.24.17 no celular do cliente  
- Webhooks adicionais: `history`, `smb_app_state_sync`, `smb_message_echoes`  
- App Review / Advanced Access antes de onboarding em massa em live mode  
- Há relatos de indisponibilidade regional / allowlist — tratar Coexistence como **objetivo**, com fallback “número só Cloud API” se o fluxo não aparecer.

---

## 4. Estado atual comprovado (22/09/2026)

| Item | Status |
|------|--------|
| Repo + FastAPI hub `/health` + `/webhook/whatsapp` | Feito |
| Python 3.12 (`.python-version`) | Feito |
| DO app Healthy · URL `https://whatsapp-meta-ph-wzewk.ondigitalocean.app` | Feito |
| Env DO: `APP_ENV`, `LOG_LEVEL`, `META_WEBHOOK_VERIFY_TOKEN`, `META_APP_SECRET`, `DATABASE_URL` | Feito |
| App Meta `PH_Softwares` · portfólio PH Softwares | Feito |
| Webhook Meta verificado + campos (ex. `messages`) | Feito |
| Número PH teste `+55 49 8411-0604` · Phone Number ID `1401420489713155` · WABA `2147274472541752` | Feito |
| Pagamento WABA PH + envio template teste BR | Feito |
| DB local `whatsapp_ph` criado (0 tabelas) · PG 9.5.0 | Feito |
| Persistência webhook no hub / pull API | **Código pronto** — deploy hub com `HUB_PULL_SECRET` + `DATABASE_URL` |
| Agente local + painel (ticket) | **Código pronto** (FASE 1–4) — seed token Meta no `.env` para envio real |
| Embedded Signup + pairing | **Scaffold** (`/onboarding` + claim) — falta config_id Meta / App Review |
| Instalador Windows | **Pendente** |
| PHVCL/GEPH | **Pendente** |
| Verificação empresa Meta / App Review Tech Provider | **Pendente** (necessário para escala) |
| Redefinir App Secret se vazou no chat | **Conferir** |

---

## 5. Stack técnica (recomendação 2026)

| Camada | Tecnologia | Motivo |
|--------|------------|--------|
| Hub + agente | FastAPI + Uvicorn + httpx + Pydantic 2 | Já no projeto; API-first; um processo no Windows |
| Painel | React + Vite (build estático servido pelo FastAPI) | SPA moderna; GEPH só abre URL |
| DB local | PostgreSQL (legado 9.5 ok) + `psycopg2` | Compatível com PHSFTW |
| Criptografia token | `cryptography` (Fernet) + chave no `.env` | Token não em claro |
| Serviço Windows | NSSM ou WinSW | Padrão para uvicorn em Server/Desktop |
| Instalador | Inno Setup | Comum em software Windows BR |
| Hub DB | Postgres gerenciado DO | Eventos webhook / pairing |
| Graph | `https://graph.facebook.com/v25.0/...` | Changelog Meta |

**Não** empacotar Django + FastAPI juntos no cliente na v1 (dois runtimes no instalador).

---

## 6. Fases de desenvolvimento (ordem obrigatória)

### FASE 0 — Conta Meta PH (parcialmente feita)

| # | Tarefa | Status |
|---|--------|--------|
| 0.1 | Business Portfolio PH Softwares | Feito |
| 0.2 | App + WhatsApp use case | Feito |
| 0.3 | Webhook → DO | Feito |
| 0.4 | Número/WABA teste PH + pagamento + envio | Feito |
| 0.5 | `META_APP_SECRET` no DO (+ redefinir se vazou) | Feito / conferir |
| 0.6 | Login for Business + config Embedded Signup | Pendente |
| 0.7 | Domínios OAuth = URL do hub DO | Pendente |
| 0.8 | Iniciar Tech Provider + App Review / Advanced Access | Pendente |
| 0.9 | Decidir Q-COEX (Coexistence) | Pendente |

---

### FASE 1 — Banco local `whatsapp_ph` + esqueleto agente

| # | Tarefa |
|---|--------|
| 1.1 | Congelar Q-DB (conexão `.env`) |
| 1.2 | `sql/001_whatsapp_ph.sql` (PG 9.5: SERIAL/BIGSERIAL) |
| 1.3 | Tabelas: `whatsapp_local_auth`, `whatsapp_config`, `whatsapp_message`, `whatsapp_webhook_event` (local mirror) |
| 1.4 | `APP_ROLE=agent` · bind `127.0.0.1:8765` |
| 1.5 | `GET /health` com `db_ok` |
| 1.6 | Auth `X-PH-Api-Key` |
| 1.7 | Seed config PH Softwares (IDs já conhecidos) + System User token **só neste PC de dev** |

**Aceite:** `\dt` ok · health 200 · status sem vazar token.

---

### FASE 2 — Envio Graph no agente (dev PH)

| # | Tarefa |
|---|--------|
| 2.1 | Cliente Graph `v25.0` (httpx) |
| 2.2 | `POST /v1/whatsapp/send-template` |
| 2.3 | `POST /v1/whatsapp/send-document` (upload media + document) |
| 2.4 | `POST /v1/whatsapp/send-text` (só com janela 24h) |
| 2.5 | `POST /v1/whatsapp/send-batch` (sequencial + backoff) |
| 2.6 | Path guard sob `PHSFTW_ROOT` + DiretorioPrincipal/Secundario |
| 2.7 | Gravar `whatsapp_message` (usuario_geph, hostname, paths, meta_message_id, ACCEPTED/FAILED) |

**Aceite:** template + PDF chegam no celular BR de teste; path fora da allowlist = 400.

**Regra Meta:** fora da janela 24h, boletos/lista = **template** aprovado ([Send messages](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages/)).

---

### FASE 3 — Hub: persistência webhook + API de pull

| # | Tarefa |
|---|--------|
| 3.1 | Hub grava POST webhook no Postgres DO (idempotência por `wamid` / id status) |
| 3.2 | Responder 200 rápido; processar async |
| 3.3 | Validar HMAC com `META_APP_SECRET` (obrigatório) |
| 3.4 | API autenticada: `GET /v1/hub/events?since=...` filtrado por `waba_id` / `installation_id` |
| 3.5 | Agente: worker poll (ex. 5–15s) → atualiza `whatsapp_message.status` (SENT/DELIVERED/READ/FAILED) |

**Aceite:** após envio, painel/DB local mostra evolução de status sem o cliente configurar webhook.

---

### FASE 4 — Painel web WHATSPH (React)

| # | Tarefa |
|---|--------|
| 4.1 | App Vite React em `web/` |
| 4.2 | Build → FastAPI serve `web/dist` em `/` |
| 4.3 | Telas: lista envios, filtros (data, usuário, status, destino), detalhe |
| 4.4 | Exibir: usuário GEPH, hostname, PDF, erros Meta |
| 4.5 | Menu GEPH: abrir `http://127.0.0.1:8765/` |

**Aceite:** histórico legível sem SQL.

Depende de **Q-LOGIN** e **Q-HIST**.

---

### FASE 5 — Embedded Signup + pairing (hub + agente)

Conforme doc Meta ([Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup/)):

| # | Tarefa |
|---|--------|
| 5.1 | Facebook Login for Business + config_id Embedded Signup no App |
| 5.2 | Página HTTPS no hub: JS SDK + callback |
| 5.3 | Receber `waba_id`, `phone_number_id`, `code` |
| 5.4 | Server-side: exchange code → business token (TTL do code ~30s) |
| 5.5 | `POST /{PHONE_NUMBER_ID}/register` (pular se Coexistence / número já registrado) |
| 5.6 | `POST /{WABA_ID}/subscribed_apps` (webhooks no app PH) |
| 5.7 | Orientar cliente a anexar pagamento na WABA dele |
| 5.8 | Pairing: blob temporário no hub → agente baixa **uma vez** → grava cifrado em `whatsapp_config` → apaga blob |
| 5.9 | GEPH: botão Conectar → browser com `installation_id` + pair code |

**Aceite:** escritório piloto conecta sem ver DigitalOcean; envio usa token **dele**.

---

### FASE 6 — Instalador Windows (cliente)

| # | Tarefa |
|---|--------|
| 6.1 | Inno Setup: perguntar pasta `PHSFTW` |
| 6.2 | Criar `{PHSFTW}\WHATSPH\` + runtime Python embed + app |
| 6.3 | Criar DB `whatsapp_ph` + aplicar SQL (mesmo cluster Postgres PH) |
| 6.4 | Gerar `installation_id`, `PH_API_KEY`, `.env` |
| 6.5 | NSSM/WinSW: serviço `PHWhatsMeta` · start automático · logs |
| 6.6 | Atalho “Painel WhatsApp PH” → `http://127.0.0.1:8765/` |
| 6.7 | Teste em Windows 10/11 e Windows Server |

**Aceite:** técnico não-Python sobe o serviço; `/health` ok.

---

### FASE 7 — PHVCL + GEPH

| # | Tarefa |
|---|--------|
| 7.1 | `WhatsMetaClient` (Indy) → `127.0.0.1:8765` |
| 7.2 | Form Conectar / Status / Abrir painel |
| 7.3 | Preview `SpeedButton6Click`: se CONECTADO → Meta; senão Whats.exe |
| 7.4 | Boletos: lote + template + PDF; passar `usuario_geph`, diretórios, telefones |
| 7.5 | Compilar PH.bpl + GEPH · CP1252 |
| 7.6 | Reusar `PermiteEnviarWhats` |

**Aceite:** boleto PDF pelo Preview via Meta; fallback Whats.exe intacto.

---

### FASE 8 — Templates, limites, manual, piloto

| # | Tarefa |
|---|--------|
| 8.1 | Modelo de template utility “boleto/relatório” (doc para o escritório aprovar na WABA) |
| 8.2 | Mensagens de erro amigáveis (códigos Meta, ex. 130497) |
| 8.3 | Manual usuário: conectar, pagamento, número, templates |
| 8.4 | Manual técnico: instalador, portas, logs |
| 8.5 | Piloto 1–2 escritórios |
| 8.6 | Verificação da empresa Meta + App Review conforme escala Tech Provider |

---

## 7. Modelo de dados (resumo)

### 7.1 Local `whatsapp_ph`

- `whatsapp_local_auth` — installation_id, api_key_hash  
- `whatsapp_config` — waba_id, phone_number_id, token_enc, status  
- `whatsapp_message` — envios + auditoria (usuário GEPH, hostname, PDF, status)  
- `whatsapp_webhook_event` — espelho local opcional / debug  

DDL detalhado: `ROTEIRO_AGENTE_LOCAL_WHATSAPP_PH.md` § / futuro `sql/001_whatsapp_ph.sql`.

### 7.2 Hub DO

- Eventos brutos webhook (JSON) + índices `waba_id`, `phone_number_id`, `message_id`  
- Pairing blobs (TTL curto)  
- Mapa `installation_id` ↔ `waba_id`  

---

## 8. Segurança

| Item | Regra |
|------|--------|
| App Secret | Só hub DO, Encrypted |
| Business token escritório | Cifrado no Postgres local; nunca log |
| API local | Loopback + API key; sem bind LAN |
| PDF | Allowlist sob PHSFTW |
| Hub pull | Auth por installation secret |
| Segredos no chat | Proibido; rotacionar se vazou |

---

## 9. Critérios de aceite finais (v1 produto)

- [ ] Escritório instala WHATSPH sem configurar Meta Developers  
- [ ] Conecta WhatsApp **dele** via Embedded Signup no hub PH  
- [ ] Envia relatório/boleto (template + PDF) pelo GEPH/PHVCL  
- [ ] Painel local mostra histórico + status (incl. retorno via hub)  
- [ ] Dois escritórios isolados (tokens/WABAs distintos)  
- [ ] Fallback Whats.exe se desconectado  
- [ ] Sem App Secret no cliente  
- [ ] Manual usuário + técnico  

---

## 10. Ordem de trabalho **agora** (próximos commits)

1. ~~Q-LOGIN-B / Q-DB2~~ — **fechadas** (ticket só pelo GEPH; DB `whatsapp_ph` conecta; schema SQL aplicado).  
2. **FASE 1 (em andamento)** — config/agent health + auth API key.  
3. **FASE 2** — envio template/PDF + fila lote.  
4. **FASE 3** — hub persist + poll status.  
5. Painel React (ticket GEPH) → Embedded Signup + Coexistence → instalador → PHVCL.

**Segurança:** senha Postgres foi exposta em chat — **trocar** a senha do role `postgres` no cluster e atualizar `.env` / sistemas PH que usam a mesma senha.

---

## 11. Riscos conhecidos

| Risco | Mitigação |
|-------|-----------|
| Webhook só HTTPS | Hub DO + poll local |
| Janela 24h | Templates para disparo em massa |
| PG 9.5 | DDL antigo; psycopg2 |
| Graph v20 EOL 24/09/2026 | Pin v25.0 |
| App Review / verificação empresa | Iniciar cedo (FASE 0.8) |
| Token temporário do painel | System User (dev) / business token Embedded Signup (cliente) |

---

## 12. Glossário rápido

| Termo | Significado |
|-------|-------------|
| WABA | WhatsApp Business Account do escritório |
| Phone Number ID | ID Graph do número (não é o telefone E.164) |
| Hub | App DigitalOcean da PH |
| Agente / WHATSPH | Serviço + painel no servidor do cliente |
| Pairing | Entrega segura token/config do hub → agente |
| Tech Provider | Cliente paga Meta; PH vende o software |

---

**Fim do roteiro mestre.** Próximo passo humano: responder as 5 perguntas Q-* da seção 3; em seguida iniciar FASE 1 no código.
