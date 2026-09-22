# Roteiro de Implementação — WhatsApp Meta Cloud API (PH Softwares)

**Data original:** 21/09/2026  
**Revisão:** 21/09/2026 (pós-deploy DigitalOcean + alinhamento arquitetura hub DO / agente local)  
**Base:** `PH_Softwares_Roteiro_WhatsApp_Meta_Cloud_API_2026.md` + respostas da PH + evidência no código PHVCL/GEPH + documentação oficial Meta + evidência de deploy.  
**Projeto Python:** `C:\projetos\python\whatsmeta`  
**Repo GitHub:** `https://github.com/danrleinascimento/whatsapp-meta-ph` (branch `main`)  
**PHVCL:** `C:\CBuilder5\Projects\Lib\phvcl`  
**Primeiro consumidor:** GEPH (demais sistemas depois, pela mesma PHVCL)

> **Regra:** só APIs oficiais Meta. Não inventar endpoints. Revalidar Graph API / Embedded Signup / limites na doc oficial no momento de cada etapa.  
> Fontes Meta usadas nesta montagem:  
> - [Partners / Tech Provider vs Solution Partner](https://developers.facebook.com/docs/whatsapp/solution-providers/)  
> - [Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup/)  
> - [Client phone numbers](https://developers.facebook.com/docs/whatsapp/embedded-signup/manage-accounts/phone-numbers/)  
> - [Migrate / Business app numbers](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/migrate-existing-whatsapp-number-to-a-business-account/)  
> - [Coexistence / Business app onboarding](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users)  
> - [Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/)

---

## 0. Estado atual comprovado (21/09/2026)

| Item | Evidência | Status |
|------|-----------|--------|
| Código hub em `C:\projetos\python\whatsmeta` | `app/main.py`, `app/webhook.py`, `app/config.py`, `Procfile`, `requirements.txt`, `.python-version` = `3.12` | Feito |
| GitHub `danrleinascimento/whatsapp-meta-ph` | commits `006da2c` (hub inicial) + `a75542a` (pin Python 3.12) | Feito |
| App DigitalOcean `whatsapp-meta-ph` | Status **Healthy**; commit live `a75542a` | Feito |
| URL pública hub | `https://whatsapp-meta-ph-wzewk.ondigitalocean.app` | Feito |
| `GET /health` | HTTP 200 → `{"status":"ok","service":"whatsapp-meta-ph","version":"0.1.0","env":"production"}` | Feito |
| `GET /webhook/whatsapp` (challenge) | Implementado; rejeita token errado com 403; sem query params → `hub.mode invalido` (esperado) | Feito |
| `POST /webhook/whatsapp` | Aceita evento, loga resumo, responde `{"status":"ok"}`; **não** persiste em DB ainda | Parcial |
| Env DO: `APP_ENV`, `LOG_LEVEL`, `META_WEBHOOK_VERIFY_TOKEN` | Presentes no build-time (log DO) | Feito |
| Env DO: `META_APP_SECRET` | **Não** comprovado no app; com secret vazio o código **não** valida HMAC (aviso em log) | Pendente |
| Componente DB DO `whatsapp-meta-db` | Criado no App Platform (~US$7/mês) | Criado |
| Uso de `DATABASE_URL` no código | Campo existe em `config.py`; **nenhuma** migration/escrita ainda | Não usado |
| App Meta (developers.facebook.com) + Webhook “Verify and save” | **Não** feito | Pendente (bloqueante agora) |
| Agente local (envio Graph, Postgres `whatsapp_ph`, API `127.0.0.1` para PHVCL) | Só planejado neste roteiro; **não** implementado | Pendente |
| PHVCL / GEPH Meta | Sem alteração Meta nesta fase | Pendente |
| Embedded Signup / pairing | Não iniciado | Pendente |

**Conclusão factual:** o **endpoint HTTPS de webhook** está no ar. O projeto **ainda não** está “ligado à Meta” nem tem o **agente local** do escritório.

**Repositório:** um só (`whatsmeta` / `whatsapp-meta-ph`). Não criar outro repo agora. O hub DO e o futuro agente local compartilham este projeto (modos/deploy distintos nas fases seguintes). PHVCL permanece em C++. Página Embedded Signup será HTTPS no hub DO (ou outro domínio PH) — **phnet não é obrigatório** para webhook.

---

## 1. Decisões alinhadas (respostas da PH + evidência técnica)

| ID | Pergunta | Resposta PH | Alinhamento técnico |
|----|----------|-------------|---------------------|
| Q1 | Billing | Escritório paga Meta direto | Compatível com **Tech Provider** (Meta fatura o cliente; PH fatura software). **Não** Solution Partner (fatura agregada). Fonte: [Partners](https://developers.facebook.com/docs/whatsapp/solution-providers/) |
| Q2 | Enquadramento | “Qual o melhor?” | **Recomendação: Tech Provider.** Motivo: sem linha de crédito; cliente adiciona cartão na WABA; processo mais curto que Solution Partner. Confirmar com Meta no cadastro do app. |
| Q3 | Número | Ver Meta | Ver §3 abaixo (oficial). |
| Q4 | Onde roda Python | `whatsmeta` local em cada máquina PH | **Híbrido (revisado):** (1) **Hub central** no DigitalOcean = webhook + (futuro) onboarding/pairing; (2) **Agente local** na máquina do escritório (PHSFTW) = envio Graph + Postgres `whatsapp_ph` + API loopback para PHVCL. Ver §4. |
| Q5 | Banco | Postgres local `whatsapp_ph` | Espelhar criação do `biph` (UTF8, `Portuguese_Brazil.1252`, owner `postgres`, porta típica `12345`). Um DB compartilhado por todos os sistemas PH na máquina. **Nota:** o Postgres gerenciado no DO (`whatsapp-meta-db`) é do **hub**; não substitui o `whatsapp_ph` local. |
| Q6 | C++ ↔ Python | Melhor / moderna / estável no Windows | **HTTP em `127.0.0.1` + API key** via Indy `TIdHTTP` (já existe na PHVCL: `TInternet1`, `Miscelan.cpp`). Sem bind em rede. Ver §5. |
| P1 | Whats.exe | Substituir, coexistir | Se Meta configurado → Cloud API; senão → `Whats.exe` atual. |
| P2 | Escopo | GEPH primeiro; desenho multi-sistema | Tela + envio na **PHVCL** (PH.bpl). |
| P3 | Caso de uso | Boleto PDF → todos arquivos pelo Preview | Ponto único: `TPreview1::SpeedButton6Click`. |
| P4 | Site / HTTPS público | Originalmente `phnet.com.br` | **Revisado:** webhook = DigitalOcean (`whatsapp-meta-ph`). Embedded Signup / OAuth = página HTTPS no **mesmo hub DO** (preferência PH) ou outro domínio PH. `phnet.com.br` **não** é obrigatório para webhook. **Nota de evidência:** PDF do fluxo atual sobe via FTP e URL pública é `https://www.ph.srv.br/RelPH/...` (`SenWA.cpp`), não phnet. phnet hoje baixa `Whats.exe`. |
| P5–P6 | Tela / cadastro | Uma config por instalação (escritório), na PHVCL | Usuário loga no PH → tela Conectar WhatsApp Meta. |
| P7 | Persistência | SQL Postgres | Sim (local `whatsapp_ph`; hub DO pode gravar eventos depois). |
| P8 | PHVCL | Sim | Preview, SenWA/NavWhats, nova unit Meta. |
| P9 | Volume | Conta Meta do escritório | Limites são da Meta (tier/qualidade), não da PH. |
| P10 | Templates | Cada escritório cria/aprova os próprios | PH só envia; não assume templates globais na v1. |
| P11 | App Meta PH | Provavelmente inexistente | **Ainda válido:** criar Business Portfolio + App + produto WhatsApp (Fase 0). |

---

## 2. Recomendação Q2 — Tech Provider (detalhe)

| | **Tech Provider** (recomendado) | **Solution Partner** |
|--|--------------------------------|----------------------|
| Cliente paga Meta | Sim | Não (paga o parceiro) |
| Linha de crédito do parceiro | Não | Sim (obrigatória) |
| Tempo para virar parceiro | Menor | Longo |
| Token pós-onboarding | Business token do cliente | System token + credit share + business token |
| Casa com Q1 da PH | **Sim** | Não |

Fontes: [Partners](https://developers.facebook.com/docs/whatsapp/solution-providers/), [Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup/).

**Pendente humano:** aceitar formalmente “PH será Tech Provider” e iniciar App Review / Advanced Access (`whatsapp_business_management`, `whatsapp_business_messaging`).

---

## 3. Números de telefone (Q3 — só o que a Meta documenta)

| Situação do número do escritório | O que a Meta permite | Observação |
|----------------------------------|----------------------|------------|
| Número no **WhatsApp pessoal (Messenger)** | **Não** usar direto na Cloud API | Precisa **apagar** a conta WhatsApp desse número e depois registrar na plataforma. Fonte: [Migrate](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/migrate-existing-whatsapp-number-to-a-business-account/) |
| Número no **WhatsApp Business App** | Pode registrar na Cloud API | Opção **Coexistence**: app + API no mesmo número (histórico 1:1 sincronizável). Exige Tech Provider/Solution Partner + Embedded Signup com `featureType: whatsapp_business_app_onboarding`. Fonte: [Onboard Business app users](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/onboarding-business-app-users) |
| Número **novo** / dedicado à API | Sim | Fluxo Embedded Signup padrão + verificação OTP + Register API |
| Já na Cloud API de outro provedor | Migração / troca de parceiro | Pode haver erro se ainda compartilha credit line antiga |

**Manual do usuário (rascunho de conteúdo):**  
1) Preferir WhatsApp **Business** App (não o app pessoal).  
2) No fluxo “Conectar”, escolher conectar número existente (Coexistence) **ou** cadastrar número novo.  
3) Após onboarding Tech Provider: anexar **forma de pagamento** na WABA (Help Center Meta: cartão na conta WhatsApp Business Platform).  
4) Sem pagamento na WABA, não envia em produção.

**Pergunta aberta à PH (D1):** na v1, habilitar **Coexistence** (Business App + API) ou só número dedicado à API?

---

## 4. Arquitetura alvo (híbrida — obrigatória por causa dos Webhooks)

A Meta exige **URL HTTPS pública** para Webhooks. Um serviço só em `localhost` **não** recebe eventos da Meta. Fonte: [Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/).

```text
┌──────────────────────────────────────────────────────────┐
│  MÁQUINA DO ESCRITÓRIO (PHSFTW)                          │
│                                                          │
│  GEPH / EFPH / ...  →  PH.bpl (Preview + tela Meta)      │
│           │                                              │
│           │ HTTP 127.0.0.1:PORTA + API key               │
│           ▼                                              │
│  Agente Python whatsmeta (Windows service / tray)        │
│           │                                              │
│           ├── Postgres local whatsapp_ph                 │
│           │     (config, tokens criptografados, msgs)    │
│           │                                              │
│           └── HTTPS outbound → graph.facebook.com        │
│                 (envio texto / media / document)         │
└───────────────────────────┬──────────────────────────────┘
                            │
                            │ HTTPS (onboarding + pairing +
                            │        opcional sync status)
                            ▼
┌──────────────────────────────────────────────────────────┐
│  HUB PH — DigitalOcean App Platform                      │
│  https://whatsapp-meta-ph-wzewk.ondigitalocean.app       │
│  (código: C:\projetos\python\whatsmeta)                  │
│                                                          │
│  • Webhook único do App Meta (todos os WABAs)  [NO AR]   │
│  • (futuro) Página Embedded Signup + OAuth/exchange      │
│  • (futuro) Pareamento: entrega token ao agente local    │
│  • App Secret só neste hub (nunca no EXE / cliente)      │
│  • Postgres gerenciado DO (eventos hub; opcional)        │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
                         META Graph API
```

### Por que o hub HTTPS público é necessário

1. **Webhooks** chegam todos no callback do App Meta; o hub identifica `waba_id` / `phone_number_id` e associa ao escritório.  
2. **Embedded Signup** precisa de domínio HTTPS + redirect URIs no App Meta.  
3. **Troca do code por token** é server-to-server com **App Secret** — App Secret **nunca** no C++ nem no pacote do cliente.

### Pareamento (token → máquina local)

Fluxo proposto (a validar na implementação; não inventar endpoints Meta — só o protocolo PH):

1. PHVCL gera `installation_id` + `pairing_code` (curto, uso único).  
2. Abre navegador: `https://whatsapp-meta-ph-wzewk.ondigitalocean.app/.../connect?install=...&pair=...` (path final a definir na Fase 3).  
3. Usuário conclui Embedded Signup.  
4. Hub DO troca code, registra número, subscribe webhooks, grava blob criptografado temporário.  
5. Agente local `whatsmeta` faz poll HTTPS autenticado e **baixa uma vez** WABA / Phone Number ID / business token → grava criptografado em `whatsapp_ph`.  
6. Blob temporário no hub expira/apaga.

**Pergunta aberta (D2):** status de entrega (SENT/DELIVERED/READ) na UI do PH:  
- (A) só “enviado à Meta” (ack do POST `/messages`) na v1, webhooks só no hub DO para auditoria; ou  
- (B) sync periódico hub DO → Postgres local para atualizar status no PH?

---

## 5. Comunicação C++ ↔ Python (Q6)

| Opção | Prós | Contras | Veredito |
|-------|------|---------|----------|
| **HTTP 127.0.0.1 + API key** | Indy já no PHVCL; simples; firewall pouco interfere no loopback; testável com curl | Precisa serviço rodando | **Escolhida** |
| Named pipes | Muito Windows-native | Mais trabalhoso no BCB5; menos tooling | Não na v1 |
| HTTPS local self-signed | Mais “bonito” | Dor de certificado no Indy BCB5 | Evitar na v1 |
| Bind `0.0.0.0` | — | Expõe API na LAN | **Proibido** |

**Contrato interno (rascunho — nomes ajustáveis; ainda não implementado):**

```text
GET  /health
GET  /v1/whatsapp/status
POST /v1/whatsapp/connect/start   → { url_onboarding, pairing }
POST /v1/whatsapp/send-text
POST /v1/whatsapp/send-document   → path PDF validado + telefone + caption
POST /v1/whatsapp/disconnect
```

Header: `X-PH-Api-Key: <chave instalação>`  
Só escuta `127.0.0.1`.

**Nota:** hoje o processo no DigitalOcean expõe `/health` e `/webhook/whatsapp` publicamente. As rotas `/v1/...` acima são do **agente local**, ainda não existem no código.

---

## 6. Estado atual no código PHVCL/GEPH (evidência — não alterar até as fases)

| Peça | Onde | Comportamento atual |
|------|------|---------------------|
| Botão Whats Preview | `phvcl\Preview.cpp` `SpeedButton6Click` | Grupo boletos ou `TSendWA1` |
| FTP + URL PDF | `phvcl\SenWA.cpp` | URL `https://www.ph.srv.br/RelPH/...` |
| Execução | `phvcl\NavWhats.cpp` | `UTEIS\Whats.exe` + `PYTHON\cache\...` |
| Telefone boleto | GEPH `CLI.WhatsApp` → `RLBol*` → `WhatsSave` | Só GEPH preenche listas de grupo |
| Login QR | GEPH `Princ` → `processarLogin` | Whats Web |

**Regra de coexistência (P1) no Preview:**

```text
se agente local status == CONECTADO (Meta)
    → envio Cloud API (documento/texto)
senão
    → fluxo atual Whats.exe
```

---

## 7. Banco Postgres

### 7.1 Local — `whatsapp_ph` (máquina do escritório)

#### Ambiente observado (evidência das telas)

| Item | Valor |
|------|--------|
| Binários | `C:\PHSFTW\POSTGRES` (pgAdmin III — cluster legado) |
| Dados | `C:\PHSFTW\DADOS` |
| Servidor | `localhost:12345` |
| DB existente | `biph` |
| Owner / encoding / locale | `postgres` / `UTF8` / `Portuguese_Brazil.1252` |

#### SQL de criação (espelho do `biph`)

```sql
CREATE DATABASE whatsapp_ph
  WITH OWNER = postgres
       ENCODING = 'UTF8'
       TABLESPACE = pg_default
       LC_COLLATE = 'Portuguese_Brazil.1252'
       LC_CTYPE = 'Portuguese_Brazil.1252'
       CONNECTION LIMIT = -1;
```

#### Tabelas lógicas (v1)

- `whatsapp_config` — 1 registro ativo por instalação (WABA, phone_number_id, status, token criptografado, datas)  
- `whatsapp_message` — envios (message_id Meta, tipo, destino, status, erro, empresa_ph opcional, sistema_origem)  
- `whatsapp_webhook_event` — se status local for sincronizado (fase posterior)  
- `whatsapp_local_auth` — API key do loopback, installation_id  

**Segurança:** senha do Postgres **não** versionar em Git; usar `.env` / DPAPI Windows para secrets.  
**Pergunta aberta (D3):** criar o database `whatsapp_ph` **agora** nesta máquina de desenvolvimento?

### 7.2 Hub — Postgres gerenciado DigitalOcean (`whatsapp-meta-db`)

- Componente já criado no App Platform.  
- Uso previsto: eventos de webhook, idempotência, blobs de pairing temporários.  
- **Ainda não** há código de acesso a DB no hub.

---

## 8. PHVCL — o que construir

| Entrega | Unit / form | Função |
|----------|-------------|--------|
| Cliente HTTP Meta local | `WhatsMetaClient.cpp/.h` | Chama `127.0.0.1` (Indy) |
| Tela configuração | `DPWhatsMeta` (TDiPad) ou similar | Status, Conectar, Testar, Desconectar — **sem** mostrar token |
| Menu | Cada Principal (GEPH primeiro) | “WhatsApp (Meta)” → abre form PHVCL |
| Preview | `Preview.cpp` | Branch Meta vs Whats.exe |
| SenWA / NavWhats | Manter | Fallback Whats.exe |
| Permissão | Já existe `PermiteEnviarWhats` | Reusar gate |

Encoding fontes: **CP1252 + CRLF** (`REGRA_CODIFICACAO.md` do GEPH — mesma regra na PHVCL).

---

## 9. Hub DigitalOcean — o que construir / status

| Entrega | Função | Status |
|---------|--------|--------|
| `GET /health` | Monitoramento DO | **Feito** |
| `GET/POST /webhook/whatsapp` | Verify challenge + HMAC + ack 200 | **Feito** (HMAC só após `META_APP_SECRET`) |
| Persistência eventos webhook | Idempotência + auditoria no DB DO | Pendente |
| Página Embedded Signup | JS SDK + config_id Login for Business | Pendente |
| Backend callback OAuth | Exchange code, register phone, subscribe_apps | Pendente |
| Endpoint pairing | Entrega segura config/token ao agente local | Pendente |
| Manual HTML/PDF do usuário | Passo a passo Meta + pagamento WABA | Pendente |

**App Meta (PH):** criar Business Portfolio, App tipo Business, produto WhatsApp, Facebook Login for Business, domínio HTTPS do hub DO, App Review / Tech Provider.

**Callback URL atual (usar no Meta Dashboard):**  
`https://whatsapp-meta-ph-wzewk.ondigitalocean.app/webhook/whatsapp`

---

## 10. Serviço Python — dois papéis no mesmo repo

Stack atual do hub (congelada no deploy): FastAPI 0.115.6 + Uvicorn 0.34.0 + Pydantic 2.10.4 + pydantic-settings + python-dotenv + httpx; Python **3.12** (`.python-version`).

### 10.1 Hub (DigitalOcean) — responsabilidades

- `/health`  
- `/webhook/whatsapp` (GET verify + POST eventos)  
- (futuro) Embedded Signup, exchange, pairing, persistência hub  

### 10.2 Agente local (máquina PHSFTW) — responsabilidades (ainda não implementadas)

- health / status no loopback  
- iniciar connect (URL onboarding)  
- poll pairing  
- send text / upload media / send document  
- validar path PDF (anti path-traversal; só pastas PH)  
- nunca logar token  
- instalar como serviço Windows (ou auto-start com o PH)  
- Postgres `whatsapp_ph`  

Envio de PDF (oficial):

```text
PDF local → POST /{PHONE_NUMBER_ID}/media → media_id
         → POST /{PHONE_NUMBER_ID}/messages type=document
```

**Janela 24h vs template:** mensagem livre só dentro da janela de atendimento; fora → template aprovado na WABA do escritório. Fonte: política WhatsApp Business.

---

## 11. Fluxos de usuário (manuais)

### 11.1 Conectar Meta (escritório)

1. Abrir sistema PH (GEPH).  
2. Menu/configuração WhatsApp (Meta).  
3. [Conectar WhatsApp].  
4. Navegador abre hub HTTPS (DO) → login Meta → Embedded Signup.  
5. Criar/selecionar Business Portfolio e WABA.  
6. Número: novo **ou** Business App (Coexistence, se habilitado).  
7. Verificar OTP.  
8. Autorizar app PH.  
9. Anexar forma de pagamento na WABA (Tech Provider).  
10. Retorna ao PH → status CONECTADO.  
11. [Testar] envia mensagem/template de teste para número do próprio escritório.

### 11.2 Enviar boleto (GEPH)

1. Preview do boleto → Whats.  
2. Se Meta CONECTADO: agente local envia PDF (media+document) para `55`+`CLI.WhatsApp`.  
3. Senão: fluxo atual FTP `ph.srv.br` + `Whats.exe`.  
4. Marcar `EnviadoPorWhatsapp` como hoje no sucesso.

### 11.3 Cadastro no Meta (resumo para o manual)

Não reproduzir telas Meta (mudam). Descrever passos oficiais e linkar Help Center / Business Suite. Incluir diferença WhatsApp pessoal vs Business App.

---

## 12. Ordem de implementação (fases) — com progresso

### Fase 0 — Conta Meta da PH (bloqueante agora)

1. Business Portfolio PH.  
2. App Meta + WhatsApp + Login for Business.  
3. Domínio HTTPS do hub DO no App (URL `whatsapp-meta-ph-wzewk.ondigitalocean.app`).  
4. Webhook: Callback URL + Verify token = `META_WEBHOOK_VERIFY_TOKEN` do DO → **Verify and save**; assinar `messages`.  
5. Copiar **App Secret** → env `META_APP_SECRET` no DigitalOcean (Encrypt) → redeploy.  
6. Iniciar caminho Tech Provider + App Review (não deixar para o fim).  
7. Decidir D1 (Coexistence) e D2 (status webhook).

### Fase 0b — Hub webhook (parcialmente concluída)

- [x] App DO + código + `/health` + `/webhook/whatsapp`  
- [ ] Ligação no Meta Dashboard (passo 4 acima)  
- [ ] `META_APP_SECRET` + validação HMAC efetiva  
- [ ] Persistência/idempotência no Postgres DO  

### Fase 1 — Postgres local + agente Python

8. Criar `whatsapp_ph`.  
9. Migrations tabelas.  
10. Modo agente local: `/health` + config `.env` + API loopback rascunho.  
11. Serviço Windows básico.

### Fase 2 — Protótipo Graph (1 WABA de teste PH)

12. Token de teste / system user.  
13. Enviar texto.  
14. Enviar PDF.  
15. Validar no Postman oficial Meta.

### Fase 3 — Hub DO: Embedded Signup + pairing (+ webhook persistente)

16. Página connect.  
17. Callback + exchange.  
18. Register number + subscribed_apps.  
19. Pairing → Postgres local.  
20. Persistência webhook no hub.

### Fase 4 — PHVCL

21. `WhatsMetaClient` (Indy).  
22. Tela Conectar/Status.  
23. Preview: branch Meta / Whats.exe.  
24. Compilar PH.bpl + GEPH.  
25. Encoding CP1252.

### Fase 5 — Templates + erros + auditoria

26. Envio template quando fora da janela.  
27. Mensagens amigáveis no C++.  
28. Logs sem segredos.  
29. Desconectar / reconectar.

### Fase 6 — Piloto e documentação

30. 1–2 escritórios piloto.  
31. Manual usuário + dev.  
32. Critérios de aceite do documento-base §58.  
33. Liberação gradual; manter Whats.exe como fallback.

---

## 13. Critérios de aceite (v1 GEPH)

- [ ] Tech Provider / App Meta configurado (ou piloto em Dev com roles no app).  
- [ ] Escritório conecta via Embedded Signup no hub HTTPS (DigitalOcean).  
- [ ] Token do escritório só no agente local criptografado / App Secret só no hub DO.  
- [ ] Texto e PDF enviados pela Cloud API.  
- [ ] Preview usa Meta se conectado; senão Whats.exe.  
- [ ] Dois escritórios (máquinas) isolados (WABA/token distintos).  
- [ ] GEPH marca boleto enviado.  
- [ ] Sem segredo Meta no EXE.  
- [ ] Documentação usuário (conectar + pagamento WABA + número).

---

## 14. Riscos e cuidados

| Risco | Mitigação |
|-------|-----------|
| Webhook em localhost | Sempre hub DigitalOcean HTTPS |
| App Secret no cliente | Nunca; só hub DO |
| WhatsApp pessoal do contador | Manual: usar Business App ou número novo |
| Cobrança | Cliente anexa cartão na WABA (TP) |
| Encoding BCB5 | CP1252 em `.cpp/.h/.dfm` |
| PDF path traversal | Validar diretórios PH |
| Coexistência Whats.exe | Feature flag por status Meta |
| Postgres antigo (pgAdmin III) | Testar driver Python compatível com a versão do cluster |
| Python default do buildpack | Manter `.python-version` = `3.12` no repo |
| HMAC desligado | Sem `META_APP_SECRET`, POST aceita sem validar assinatura — preencher após criar App Meta |

---

## 15. OPEN QUESTIONS (não codificar sem resposta)

| ID | Pergunta | Impacto |
|----|----------|---------|
| **D1** | V1 com **Coexistence** (Business App + API) ou só número dedicado? | Fluxo Embedded Signup / manual |
| **D2** | Status DELIVERED/READ na UI do PH na v1? (A) só ack envio (B) sync webhook hub DO→local | Escopo Python/hub |
| **D3** | Criar `whatsapp_ph` **agora** neste PC? | Fase 1 |
| **D4** | Embedded Signup no **próprio app DO** (recomendado agora) ou em outro domínio PH? Stack web disponível? | Fase 3 — **phnet não é mais premissa** |
| **D5** | Porta local do agente (ex. `8765`) e forma de instalação (serviço Windows vs iniciar com o GEPH)? | Deploy |
| **D6** | “Cadastro único” = **1 WABA por instalação/escritório** (confirmado). Precisa campo `empresa_id` GEPH nos logs mesmo assim (multi-empresa no mesmo EXE)? | Modelo de dados |
| **D7** | PDF no Meta: enviar **arquivo binário** na Cloud API (recomendado) ou continuar só **link** `ph.srv.br` como no Whats.exe? | UX + mídia |

---

## 16. Próximo passo imediato (atualizado)

**Feito:** hub webhook no DigitalOcean + código em `C:\projetos\python\whatsmeta`.

**Agora (único passo bloqueante):**

1. Abrir [Meta Developers → Apps](https://developers.facebook.com/apps/).  
2. Criar (ou abrir) o App da PH com produto **WhatsApp**.  
3. **WhatsApp → Configuration → Webhook:**  
   - Callback URL: `https://whatsapp-meta-ph-wzewk.ondigitalocean.app/webhook/whatsapp`  
   - Verify token: o mesmo `META_WEBHOOK_VERIFY_TOKEN` do DigitalOcean  
   - **Verify and save**  
4. Assinar o campo **`messages`**.  
5. Em **Settings → Basic**, copiar o **App Secret** → colar como `META_APP_SECRET` (Encrypt) no DigitalOcean → redeploy.  
6. Enviar print da tela do Webhook verificado.

**Não** iniciar ainda: PHVCL, agente local de envio, Embedded Signup, criar `whatsapp_ph` — até o challenge da Meta passar.

**Não** alterar PHVCL/GEPH sem aprovação explícita da Fase 0 concluída (webhook Meta OK).
