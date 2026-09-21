# Roteiro de Implementação — WhatsApp Meta Cloud API (PH Softwares)

**Data:** 21/09/2026  
**Base:** `PH_Softwares_Roteiro_WhatsApp_Meta_Cloud_API_2026.md` + respostas da PH + evidência no código PHVCL/GEPH + documentação oficial Meta.  
**Projeto Python:** `C:\projetos\python\whatsmeta`  
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

## 1. Decisões alinhadas (respostas da PH + evidência técnica)

| ID | Pergunta | Resposta PH | Alinhamento técnico |
|----|----------|-------------|---------------------|
| Q1 | Billing | Escritório paga Meta direto | Compatível com **Tech Provider** (Meta fatura o cliente; PH fatura software). **Não** Solution Partner (fatura agregada). Fonte: [Partners](https://developers.facebook.com/docs/whatsapp/solution-providers/) |
| Q2 | Enquadramento | “Qual o melhor?” | **Recomendação: Tech Provider.** Motivo: sem linha de crédito; cliente adiciona cartão na WABA; processo mais curto que Solution Partner. Confirmar com Meta no cadastro do app. |
| Q3 | Número | Ver Meta | Ver §3 abaixo (oficial). |
| Q4 | Onde roda Python | `whatsmeta` local em cada máquina PH | Serviço local + onboarding/webhooks **centrais** em HTTPS (`phnet.com.br`) — ver §4. |
| Q5 | Banco | Postgres local `whatsapp_ph` | Espelhar criação do `biph` (UTF8, `Portuguese_Brazil.1252`, owner `postgres`, porta típica `12345`). Um DB compartilhado por todos os sistemas PH na máquina. |
| Q6 | C++ ↔ Python | Melhor / moderna / estável no Windows | **HTTP em `127.0.0.1` + API key** via Indy `TIdHTTP` (já existe na PHVCL: `TInternet1`, `Miscelan.cpp`). Sem bind em rede. Ver §5. |
| P1 | Whats.exe | Substituir, coexistir | Se Meta configurado → Cloud API; senão → `Whats.exe` atual. |
| P2 | Escopo | GEPH primeiro; desenho multi-sistema | Tela + envio na **PHVCL** (PH.bpl). |
| P3 | Caso de uso | Boleto PDF → todos arquivos pelo Preview | Ponto único: `TPreview1::SpeedButton6Click`. |
| P4 | Site | `https://www.phnet.com.br/` | Usar para Embedded Signup + Webhooks. **Nota de evidência:** PDF do fluxo atual sobe via FTP e URL pública é `https://www.ph.srv.br/RelPH/...` (`SenWA.cpp`), não phnet. phnet hoje baixa `Whats.exe`. |
| P5–P6 | Tela / cadastro | Uma config por instalação (escritório), na PHVCL | Usuário loga no PH → tela Conectar WhatsApp Meta. |
| P7 | Persistência | SQL Postgres | Sim. |
| P8 | PHVCL | Sim | Preview, SenWA/NavWhats, nova unit Meta. |
| P9 | Volume | Conta Meta do escritório | Limites são da Meta (tier/qualidade), não da PH. |
| P10 | Templates | Cada escritório cria/aprova os próprios | PH só envia; não assume templates globais na v1. |
| P11 | App Meta PH | Provavelmente inexistente | Fase 0: criar Business Portfolio + App + WhatsApp product. |

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
│  MÁQUINA DO ESCRITÓRIO                                   │
│                                                          │
│  GEPH / EFPH / ...  →  PH.bpl (Preview + tela Meta)      │
│           │                                              │
│           │ HTTP 127.0.0.1:PORTA + API key               │
│           ▼                                              │
│  Serviço Python whatsmeta (Windows service / tray)       │
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
│  CENTRO PH — https://www.phnet.com.br/                   │
│                                                          │
│  • Página Embedded Signup (JS SDK + Login for Business)  │
│  • Callback OAuth / exchange code → business token       │
│  • Webhook único do App Meta (todos os WABAs)            │
│  • Pareamento: entrega token/config ao agente local      │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
                         META Graph API
```

### Por que o centro em phnet é necessário

1. **Embedded Signup** precisa de domínio HTTPS + redirect URIs no App Meta.  
2. **Webhooks** chegam todos no callback do App; depois o centro identifica `waba_id` / `phone_number_id` e associa ao escritório.  
3. **Troca do code por token** é server-to-server com **App Secret** — App Secret **nunca** no C++ nem no pacote do cliente.

### Pareamento (token → máquina local)

Fluxo proposto (a validar na implementação; não inventar endpoints Meta — só o protocolo PH):

1. PHVCL gera `installation_id` + `pairing_code` (curto, uso único).  
2. Abre navegador: `https://www.phnet.com.br/.../whatsapp/connect?install=...&pair=...`  
3. Usuário conclui Embedded Signup.  
4. Servidor phnet troca code, registra número, subscribe webhooks, grava blob criptografado temporário.  
5. Serviço local `whatsmeta` faz poll HTTPS autenticado e **baixa uma vez** WABA / Phone Number ID / business token → grava criptografado em `whatsapp_ph`.  
6. Blob temporário no phnet expira/apaga.

**Pergunta aberta (D2):** status de entrega (SENT/DELIVERED/READ) na UI do PH:  
- (A) só “enviado à Meta” (ack do POST `/messages`) na v1, webhooks só no phnet para auditoria; ou  
- (B) sync periódico phnet → Postgres local para atualizar status no PH?

---

## 5. Comunicação C++ ↔ Python (Q6)

| Opção | Prós | Contras | Veredito |
|-------|------|---------|----------|
| **HTTP 127.0.0.1 + API key** | Indy já no PHVCL; simples; firewall pouco interfere no loopback; testável com curl | Precisa serviço rodando | **Escolhida** |
| Named pipes | Muito Windows-native | Mais trabalhoso no BCB5; menos tooling | Não na v1 |
| HTTPS local self-signed | Mais “bonito” | Dor de certificado no Indy BCB5 | Evitar na v1 |
| Bind `0.0.0.0` | — | Expõe API na LAN | **Proibido** |

**Contrato interno (rascunho — nomes ajustáveis):**

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

---

## 6. Estado atual no código (evidência — não alterar até as fases)

| Peça | Onde | Comportamento atual |
|------|------|---------------------|
| Botão Whats Preview | `phvcl\Preview.cpp` `SpeedButton6Click` | Grupo boletos ou `TSendWA1` |
| FTP + URL PDF | `phvcl\SenWA.cpp` | URL `https://www.ph.srv.br/RelPH/...` |
| Execução | `phvcl\NavWhats.cpp` | `UTEIS\Whats.exe` + `PYTHON\cache\...` |
| Telefone boleto | GEPH `CLI.WhatsApp` → `RLBol*` → `WhatsSave` | Só GEPH preenche listas de grupo |
| Login QR | GEPH `Princ` → `processarLogin` | Whats Web |

**Regra de coexistência (P1) no Preview:**

```text
se whatsmeta status == CONECTADO (Meta)
    → envio Cloud API (documento/texto)
senão
    → fluxo atual Whats.exe
```

---

## 7. Banco Postgres `whatsapp_ph`

### Ambiente observado (evidência das telas)

| Item | Valor |
|------|--------|
| Binários | `C:\PHSFTW\POSTGRES` (pgAdmin III — cluster legado) |
| Dados | `C:\PHSFTW\DADOS` |
| Servidor | `localhost:12345` |
| DB existente | `biph` |
| Owner / encoding / locale | `postgres` / `UTF8` / `Portuguese_Brazil.1252` |

### SQL de criação (espelho do `biph`)

```sql
CREATE DATABASE whatsapp_ph
  WITH OWNER = postgres
       ENCODING = 'UTF8'
       TABLESPACE = pg_default
       LC_COLLATE = 'Portuguese_Brazil.1252'
       LC_CTYPE = 'Portuguese_Brazil.1252'
       CONNECTION LIMIT = -1;
```

### Tabelas lógicas (v1)

- `whatsapp_config` — 1 registro ativo por instalação (WABA, phone_number_id, status, token criptografado, datas)  
- `whatsapp_message` — envios (message_id Meta, tipo, destino, status, erro, empresa_ph opcional, sistema_origem)  
- `whatsapp_webhook_event` — se status local for sincronizado (fase posterior)  
- `whatsapp_local_auth` — API key do loopback, installation_id  

**Segurança:** senha do Postgres **não** versionar em Git; usar `.env` / DPAPI Windows para secrets.  
**Pergunta aberta (D3):** criar o database `whatsapp_ph` **agora** nesta máquina de desenvolvimento?

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

## 9. Portal phnet — o que construir

| Entrega | Função |
|---------|--------|
| Página Embedded Signup | JS SDK + config_id Login for Business |
| Backend callback | Exchange code, register phone, subscribe_apps |
| Endpoint pairing | Entrega segura config/token ao agente local |
| Webhook `/webhook/whatsapp` | Verify challenge + HMAC + idempotência |
| Manual HTML/PDF do usuário | Passo a passo Meta + pagamento WABA |

**App Meta (PH):** criar Business Portfolio, App tipo Business, produto WhatsApp, Facebook Login for Business, domínios HTTPS, App Review.

---

## 10. Serviço Python local (`C:\projetos\python\whatsmeta`)

Stack a avaliar na Fase 3 (sem fechar versão sem checar ambiente do cliente): FastAPI + Uvicorn + httpx + Pydantic + driver Postgres + cryptography.

Responsabilidades locais:

- health / status  
- iniciar connect (URL onboarding)  
- poll pairing  
- send text / upload media / send document  
- validar path PDF (anti path-traversal; só pastas PH)  
- nunca logar token  
- instalar como serviço Windows (ou auto-start com o PH)

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
4. Navegador abre phnet → login Meta → Embedded Signup.  
5. Criar/selecionar Business Portfolio e WABA.  
6. Número: novo **ou** Business App (Coexistence, se habilitado).  
7. Verificar OTP.  
8. Autorizar app PH.  
9. Anexar forma de pagamento na WABA (Tech Provider).  
10. Retorna ao PH → status CONECTADO.  
11. [Testar] envia mensagem/template de teste para número do próprio escritório.

### 11.2 Enviar boleto (GEPH)

1. Preview do boleto → Whats.  
2. Se Meta CONECTADO: `whatsmeta` envia PDF (media+document) para `55`+`CLI.WhatsApp`.  
3. Senão: fluxo atual FTP `ph.srv.br` + `Whats.exe`.  
4. Marcar `EnviadoPorWhatsapp` como hoje no sucesso.

### 11.3 Cadastro no Meta (resumo para o manual)

Não reproduzir telas Meta (mudam). Descrever passos oficiais e linkar Help Center / Business Suite. Incluir diferença WhatsApp pessoal vs Business App.

---

## 12. Ordem de implementação (fases)

### Fase 0 — Conta Meta da PH (bloqueante)

1. Business Portfolio PH.  
2. App Meta + WhatsApp + Login for Business.  
3. Domínio `phnet.com.br` no App.  
4. Webhook de teste.  
5. Iniciar caminho Tech Provider + App Review (não deixar para o fim).  
6. Decidir D1 (Coexistence) e D2 (status webhook).

### Fase 1 — Postgres + esqueleto Python local

7. Criar `whatsapp_ph`.  
8. Migrations tabelas.  
9. FastAPI `/health` + config `.env`.  
10. Serviço Windows básico.

### Fase 2 — Protótipo Graph (1 WABA de teste PH)

11. Token de teste / system user.  
12. Enviar texto.  
13. Enviar PDF.  
14. Validar no Postman oficial Meta.

### Fase 3 — phnet: Embedded Signup + pairing + webhook

15. Página connect.  
16. Callback + exchange.  
17. Register number + subscribed_apps.  
18. Pairing → Postgres local.  
19. Webhook central.

### Fase 4 — PHVCL

20. `WhatsMetaClient` (Indy).  
21. Tela Conectar/Status.  
22. Preview: branch Meta / Whats.exe.  
23. Compilar PH.bpl + GEPH.  
24. Encoding CP1252.

### Fase 5 — Templates + erros + auditoria

25. Envio template quando fora da janela.  
26. Mensagens amigáveis no C++.  
27. Logs sem segredos.  
28. Desconectar / reconectar.

### Fase 6 — Piloto e documentação

29. 1–2 escritórios piloto.  
30. Manual usuário + dev.  
31. Critérios de aceite do documento-base §58.  
32. Liberação gradual; manter Whats.exe como fallback.

---

## 13. Critérios de aceite (v1 GEPH)

- [ ] Tech Provider / App Meta configurado (ou piloto em Dev com roles no app).  
- [ ] Escritório conecta via Embedded Signup no phnet.  
- [ ] Token só no servidor local criptografado / App Secret só no phnet.  
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
| Webhook em localhost | Sempre phnet HTTPS |
| App Secret no cliente | Nunca; só phnet |
| WhatsApp pessoal do contador | Manual: usar Business App ou número novo |
| Cobrança | Cliente anexa cartão na WABA (TP) |
| Encoding BCB5 | CP1252 em `.cpp/.h/.dfm` |
| PDF path traversal | Validar diretórios PH |
| Coexistência Whats.exe | Feature flag por status Meta |
| Postgres antigo (pgAdmin III) | Testar driver Python compatível com a versão do cluster |

---

## 15. OPEN QUESTIONS (não codificar sem resposta)

| ID | Pergunta | Impacto |
|----|----------|---------|
| **D1** | V1 com **Coexistence** (Business App + API) ou só número dedicado? | Fluxo Embedded Signup / manual |
| **D2** | Status DELIVERED/READ na UI do PH na v1? (A) só ack envio (B) sync webhook phnet→local | Escopo Python/phnet |
| **D3** | Criar `whatsapp_ph` **agora** neste PC? | Fase 1 |
| **D4** | Quem hospeda/implanta o backend Embedded Signup no **phnet.com.br** (time web PH)? Já existe stack (ASP/PHP/Node)? | Fase 3 |
| **D5** | Porta local do whatsmeta (ex. `8765`) e forma de instalação (serviço Windows vs iniciar com o GEPH)? | Deploy |
| **D6** | “Cadastro único” = **1 WABA por instalação/escritório** (confirmado). Precisa campo `empresa_id` GEPH nos logs mesmo assim (multi-empresa no mesmo EXE)? | Modelo de dados |
| **D7** | PDF no Meta: enviar **arquivo binário** na Cloud API (recomendado) ou continuar só **link** `ph.srv.br` como no Whats.exe? | UX + mídia |

---

## 16. Próximo passo imediato

1. Você responde **D1–D7**.  
2. Congelamos este roteiro.  
3. Só então: criar DB (se D3=sim) → esqueleto Python → conta Meta → PHVCL.

**Não iniciar alteração em PHVCL/GEPH/código Meta sem aprovação explícita da Fase 0/1.**
