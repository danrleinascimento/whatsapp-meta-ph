# Roteiro de Implementação — Produto WhatsApp PH (serviço + painel WHATSPH)

**Data:** 22/09/2026  
**Revisão:** alinhamento com visão completa (envio + retorno + painel web local)  
**Projeto código:** `C:\projetos\python\whatsmeta`  
**Pasta no cliente (alvo):** `{PHSFTW}\WHATSPH\`  
**DB local:** `whatsapp_ph` @ Postgres do PHSFTW (`localhost:12345`, PG **9.5.0**)  
**Hub nuvem:** DigitalOcean `whatsapp-meta-ph` (webhook Meta — **já no ar**)

> Fontes: Meta Embedded Signup / Webhooks / Send messages / Templates / Media; Graph changelog; NSSM; FastAPI+React SPA (prática 2026).

---

## 0. Sua pergunta: “tem como fazer isso?”

**Sim.** É um produto com **três peças**, não uma só:

| Peça | Função | Onde roda |
|------|--------|-----------|
| **1. Hub PH** | Webhook Meta + Embedded Signup (HTTPS) + fila de eventos por escritório | DigitalOcean (já existe o webhook) |
| **2. Serviço Windows** | Envio Graph (texto/template/PDF/lote) + **puxa** status do hub + grava no Postgres | Máquina do escritório |
| **3. Painel web WHATSPH** | Consultar envios, PDFs, status, usuário GEPH, máquina, data | Browser local (`127.0.0.1`) aberto pelo menu do GEPH |

O GEPH **não** precisa reimplementar a UI de histórico: só abre o navegador em  
`http://127.0.0.1:8765/` (ou porta fixa do painel) e chama a API de envio em background.

---

## 1. Por que o “retorno” não chega direto no PC do cliente

A Meta **só** envia webhook para URL **HTTPS pública**.  
Máquina do escritório / `localhost` **não** recebe POST da Meta. Fonte: [Webhooks Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks/).

Fluxo correto (padrão on-prem + cloud ingress):

```text
Meta --POST webhook--> Hub DigitalOcean
                         | grava evento (waba_id, phone_number_id, statuses)
                         | responde 200 rápido
                         v
Serviço local WHATSPH --HTTPS periodicamente--> Hub
                         | "me dê eventos do meu installation_id / waba_id"
                         | autenticação (chave de instalação)
                         v
                    Postgres whatsapp_ph
                         |
                         v
                    Painel React (lista / detalhe / status)
```

**Decisão L2 (sua escolha “quero tudo”):** implementar **envio + retorno**, com retorno via **hub → poll do agente local** (não via Meta → localhost).

Alternativa “hub faz push para IP do cliente” **não** funciona na prática (NAT, IP dinâmico, firewall). Poll autenticado é o caminho padrão.

---

## 2. Stack recomendada (pesquisa 22/09/2026) — **não Django + FastAPI juntos**

Você sugeriu Django + React. Dá, mas no **mesmo instalador Windows** com PG 9.5 + serviço único, isso vira **dois frameworks Python** (dois mundos, dois deploys, mais falha).

| Opção | Prós | Contras | Veredito |
|-------|------|---------|----------|
| **FastAPI (API+serviço) + React (Vite) no mesmo processo** | Um serviço Windows; já temos FastAPI no `whatsmeta`/hub; React SPA moderna; servir `dist/` pelo FastAPI | Admin “grátis” do Django não vem de fábrica | **Recomendado** |
| Django + DRF + React | Admin pronto | Segundo stack; mais pesado no instalador; duplica modelo com o agente | Evitar na v1 |
| FastAPI + Django juntos | — | Operação de dois apps no cliente | **Não** |

**Decisão de arquitetura (recomendada):**

- Backend: **FastAPI** (envio + poll hub + API do painel + static React)  
- Frontend: **React + Vite**  
- Pasta: `{PHSFTW}\WHATSPH\`  
- Serviço: **um** Windows Service (NSSM/WinSW)  
- DB: **um** `whatsapp_ph`

Isso atende: menu GEPH abre o painel; histórico completo; instalador simples.

> Se no futuro quiser Django Admin interno PH, pode ser ferramenta **só na PH**, não no pacote do cliente.

---

## 3. O que o painel WHATSPH mostra (requisito seu → modelo)

Cada envio grava (mínimo):

| Campo | Origem |
|-------|--------|
| `meta_message_id` | resposta Graph |
| `status` | ACCEPTED → SENT → DELIVERED → READ / FAILED (via webhook sync) |
| `to_wa_id` | destinatário |
| `msg_type` | text / document / template |
| `caption` / template vars | texto |
| `local_file_path` / nome PDF | path validado |
| `sistema_origem` | GEPH / EFPH / … |
| `usuario_geph` | login do usuário no sistema PH (GEPH passa no POST) |
| `empresa_id_ref` | opcional |
| `hostname` / `machine_name` | agente preenche (`socket.gethostname()`) |
| `installation_id` | instalador |
| `created_at` / `updated_at` | timestamps |

Lista, filtro por período, usuário, status, abrir detalhe do PDF (path local se ainda existir).

---

## 4. Pasta no cliente

```text
C:\PHSFTW\                    (ou caminho escolhido no instalador)
  POSTGRES\ ...
  DADOS\ ...
  WHATSPH\                    ← produto WhatsApp PH
    app\                      ← backend FastAPI (ou binários)
    web\dist\                 ← React build
    .env                      ← segredos locais (não na nuvem)
    logs\
    nssm\ / winsw\            ← wrapper do serviço
```

Nome da pasta: **`WHATSPH`** (você escreveu WHATSPH; confirme se prefere outro nome).

---

## 5. Fluxos de usuário

### 5.1 Conectar WhatsApp

1. Menu GEPH → “WhatsApp / Conectar”  
2. Abre browser: hub DO Embedded Signup (+ `installation_id` + pairing)  
3. Hub troca code→token (App Secret **só no DO**)  
4. Agente local faz poll/pairing e grava token **cifrado** em `whatsapp_config`  
5. Painel mostra status CONECTADO  

### 5.2 Enviar relatório / boleto

1. Preview PHVCL / boletos → texto + PDF + lista  
2. GEPH POST `127.0.0.1:8765/v1/whatsapp/send-batch` com `usuario_geph`, paths, destinatários  
3. Agente valida path sob `PHSFTW` / diretórios PH  
4. Fora da janela 24h → **template** utility (regra Meta)  
5. Grava linhas em `whatsapp_message`  
6. Poll hub atualiza status  

### 5.3 Consultar histórico

1. Menu GEPH → “WhatsApp / Painel”  
2. Abre `http://127.0.0.1:8765/` (React)  
3. Lista / filtros / detalhe  

---

## 6. Decisões já fechadas

| ID | Decisão |
|----|---------|
| L1 | Porta API/painel base **8765** |
| L2 | Envio **e** retorno (sync via hub poll) |
| L3 | PDF via upload `media_id` |
| L8 | Graph **`v25.0`** (evitar v20 — fim 24/09/2026) |
| Stack painel | **FastAPI + React**, **não** Django no cliente v1 |
| Bind | `127.0.0.1` apenas |

---

## 7. Fases (ordem — não pular)

| Fase | Escopo |
|------|--------|
| **P0** | Congelar dúvidas §9 |
| **P1** | SQL `whatsapp_ph` + agente send (template/PDF) + health |
| **P2** | Hub: persistir webhooks + API “pull events” autenticada |
| **P3** | Agente: worker poll → atualiza `whatsapp_message.status` |
| **P4** | React painel (lista/detalhe) servido pelo FastAPI |
| **P5** | Embedded Signup + pairing no hub |
| **P6** | Instalador Inno + NSSM → pasta WHATSPH + serviço + DB |
| **P7** | PHVCL/GEPH: menu + POST envio + abrir browser |

---

## 8. Critérios de aceite (produto)

- [ ] Instalador cria WHATSPH + serviço + DB  
- [ ] GEPH envia PDF+texto/lote via localhost  
- [ ] Status evolui até DELIVERED/READ/FAILED (quando Meta enviar webhook)  
- [ ] Painel mostra usuário GEPH, máquina, destino, PDF, datas  
- [ ] Conectar WhatsApp via browser hub DO  
- [ ] Sem App Secret no cliente  

---

## 9. Perguntas em aberto (responda no chat)

1. Pasta no cliente: confirmar nome **`WHATSPH`** dentro de `PHSFTW`?  
2. Stack: aceita **FastAPI + React** (recomendado) em vez de Django no cliente?  
3. Login do **painel web**:  
   - **(W)** sem senha extra (só quem está na máquina / rede local loopback), ou  
   - **(U)** login com o **mesmo usuário do GEPH** (GEPH passa token/sessão ao abrir), ou  
   - **(S)** senha própria do WHATSPH?  
4. Vários usuários GEPH no **mesmo** servidor: histórico **compartilhado do escritório** ou cada um só vê o que **ele** enviou (com filtro admin)?  
5. Confirma porta única **8765** para API **e** painel (React no mesmo host)?  
6. Boletos em massa: aceita **template aprovado** fora da janela 24h (obrigação Meta)?  
7. Ainda pendente: `DATABASE_URL` neste PC — consegue conectar no `whatsapp_ph` com o user `postgres` do `biph`? (sim/não, sem colar senha)

Com isso, congelamos e começamos **P1** (SQL + envio).
