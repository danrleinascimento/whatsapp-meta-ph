# WhatsApp Meta PH — documentação do projeto

Documento para o próximo programador ou IA. Descreve o que o código faz, o que já está pronto, o que ainda falta e como ele se liga aos outros sistemas da PH Softwares.

Data desta descrição: **25/09/2026**. Atualização em **19/10/2026**: porta do agente 8765 → 8767 (seção 13). Atualização em **26/10/2026**: `whatsph.exe` e serviço em `PHSFTW\SERVICOS\WHATSPH` (seção 14).  
Código: `C:\projetos\python\whatsmeta`  
Repositório: https://github.com/danrleinascimento/whatsapp-meta-ph  
Hub em produção: https://whatsapp-meta-ph-wzewk.ondigitalocean.app  
Versão do processo local conferida nesta sessão: **0.2.4** (`GET /health`).

O `README.md` desta pasta é um resumo de endpoints e de como subir o agente. A tabela “Fases ainda humanas” do README está **atrasada**: o cliente C++ e os modelos de PDF já existem (ver seções 7 e 11). Este arquivo é a descrição completa.

Não há segredos aqui. Tokens, senhas e `META_APP_SECRET` ficam só no `.env` (não versionado).

---

## 1. O que é

Um único programa Python (FastAPI) com dois papéis, escolhidos pela variável `APP_ROLE`:

| Papel | Onde roda | Para que serve |
|-------|-----------|----------------|
| `hub` | DigitalOcean (URL acima) | Receber o webhook da Meta, guardar eventos e entregar esses eventos ao escritório. Também tem a página de cadastro embutido (Embedded Signup), ainda sem `config_id`. |
| `agent` | PC do escritório, só em `127.0.0.1:8767` | Enviar PDF e texto pela Graph API, gravar o envio no Postgres local, puxar os eventos do hub e servir o painel “Acompanhar envios”. |

O GEPH (C++ Builder 5) **não** fala com a Meta. Ele fala só com o agente local. O agente fala com a Graph API e com o hub. A Meta fala só com o hub (URL pública).

Nome interno do agente no escritório: **WHATSPH**. Serviço Windows: `PHWhatsMeta`, registrado pelo próprio `whatsph.exe` em `PHSFTW\SERVICOS\WHATSPH` desde 26/10/2026 (antes era NSSM; ver seção 14). Em 25/09/2026 o serviço estava **parado** e quem atendia a porta (então 8765) era o uvicorn do venv deste repositório.

**Porta do agente: 8767 desde 19/10/2026** (antes 8765). A 8765 passou a ser do serviço HUPH (`C:\PHSFTW\SERVICOS\HUPH\huph.exe`, `127.0.0.1:8765`), usado pela Central RTPH. Detalhes na seção 13.

---

## 2. O que ele faz

1. Sobe um PDF na Graph API e manda para um celular.
2. Escolhe o modo de envio:
   - **Sessão** (mensagem livre com documento): só chega se o destinatário tiver escrito para o número da empresa nas últimas 24 horas.
   - **Modelo** (template): obrigatório fora dessa janela. O modelo precisa estar `APPROVED` na WABA e ter cabeçalho do tipo `DOCUMENT`.
3. Grava cada envio em `whatsapp_message` com status inicial `ACCEPTED` e o `wamid` devolvido pela Meta.
4. A cada 10 segundos puxa eventos do hub e, se houver recibo `sent` / `delivered` / `read` / `failed`, atualiza a mesma linha.
5. Abre um painel web (React) com ticket HMAC para o contador acompanhar os envios, sem ver token da Meta.
6. No hub, valida a assinatura `X-Hub-Signature-256` do webhook.

`ACCEPTED` no painel aparece como **Aceito pela Meta**. Isso significa que a Graph API aceitou o pedido. Não significa que o celular recebeu.

---

## 3. Conta Meta em uso (25/09/2026)

| Item | Valor |
|------|--------|
| App | PH_Softwares, id `2053406131958490` |
| Negócio | PH Softwares, id `229667012086101` |
| WABA | `2147274472541752` |
| `phone_number_id` | `1401420489713155` |
| Número exibido | +55 49 8411-0604 (`verified_name` PH Softwares Ltda) |
| `installation_id` local | `local-dev` |
| Webhook | `https://whatsapp-meta-ph-wzewk.ondigitalocean.app/webhook/whatsapp` |
| Campo assinado | `messages` (e outros de conta; não desligar) |
| App inscrito na WABA | sim, desde 24/09/2026 (`POST /{WABA}/subscribed_apps` → `success`) |
| App publicado | **não** |
| Verificação da empresa | em processamento |
| Domínio `phsoftwares.com.br` | não verificado no Gerenciador de Negócios |
| `META_EMBEDDED_SIGNUP_CONFIG_ID` no hub | vazio (o botão Conectar do painel avisa que o cadastro ainda não está liberado) |

A conta já está **conectada por seed** no Postgres local (`scripts/seed_dev_config.py` + token no `.env`). O fluxo “Conectar” do GEPH não é necessário para os envios atuais.

Graph API usada pelo código: versão configurada no projeto (v25 nas chamadas do agente). O painel da Meta mostrava o campo `messages` na v26.0; isso não muda o contrato do webhook de status.

---

## 4. Projetos parceiros e ligações

```text
Celular do cliente
    |  mensagem do cliente abre a janela de 24 h
    v
Meta Cloud API  (app PH_Softwares)
    |  webhook statuses + mensagens recebidas
    v
Hub DigitalOcean  APP_ROLE=hub
    |  GET /v1/hub/events  (header X-PH-Hub-Secret, a cada 10 s)
    v
Agente local  127.0.0.1:8767  APP_ROLE=agent
    |  Postgres local  whatsapp_ph
    |  painel React  /?ticket=
    ^
    |  HTTP JSON  X-PH-Api-Key
WhatsMetaClient  (PH.bpl, C++ Builder 5, CP1252)
    ^
GEPH.exe  e outros sistemas PH que usam o mesmo PH.bpl
```

| Parceiro | Pasta | Ligação |
|----------|-------|---------|
| **GEPH** | `C:\CBuilder5\Projects\GEPH` | Menus Ferramentas: Situação da conta, Acompanhar envios, Conectar. Preview: botão WhatsApp. Histórico: `ajustesrealizados.md` §21 |
| **PHVCL** | `C:\CBuilder5\Projects\Lib\phvcl` | `WhatsMetaClient.cpp/.h` (HTTP), `WhatsMetaUi` (diálogos), `Preview.cpp` (grupo de boletos), `SenWA.cpp` (relatório avulso). Outros sistemas PH herdam isso ao recompilar o `PH.bpl` |
| **Hub** | este mesmo código, `APP_ROLE=hub` | DigitalOcean. Webhook, pull, migrate, onboarding |
| **Postgres local** | banco `whatsapp_ph` | Config, mensagens, estado do poller. O agente exige `schema_ok` |
| **Postgres do hub** | gerenciado na DigitalOcean | Deveria ter `whatsapp_webhook_event`. Em 25/09/2026 o usuário do app **não** tem `CREATE` em `public`. Eventos ficam na memória do processo |
| **Whats.exe** | `{PHSFTW}\UTEIS\Whats.exe` | Canal **antigo** (Chrome + WhatsApp Web). O GEPH só cai nele quando a conta oficial está desconectada. Não misturar com este projeto |
| **Cópias de instalação** | `C:\PHSFTW\SERVICOS\WHATSPH` (atual, desde 26/10/2026); `C:\PHSFTW\WHATSPH` e `D:\PHSFTW\WHATSPH` (antigas, do NSSM) | A atual tem `whatsph.exe`, `.env` e `logs\`. As antigas não rodam mais nada; a de `C:` ainda guarda o `.env` que o GEPH sem Rebuild lê (mesmas chaves). Ver seção 14 |
| **GitHub** | `danrleinascimento/whatsapp-meta-ph` | O commit antigo `82218a6` está em `main`. O trabalho do agente e do C++ desta sessão **não** foi enviado ao remoto (só commitar se o usuário pedir) |

O GEPH guarda clientes em arquivo binário (`PHTable`), não neste Postgres. O telefone de 11 dígitos do cadastro (`CLI.WhatsApp`) é lido pelo C++ e enviado como `55` + 11 dígitos. A Graph API pode devolver `wa_id` sem o nono dígito. O aparelho de teste usado foi +55 49 99818-5612; no banco local o número é `5549998185612`.

---

## 5. Mapa do código

| Caminho | Função |
|---------|--------|
| `app/main.py` | Sobe hub ou agente. No agente inicia o poller. Monta `web/dist/assets` |
| `app/config.py` | Lê o `.env`. Nomes dos modelos: `WHATSAPP_BOLETO_TEMPLATE_*` e `WHATSAPP_RELATORIO_TEMPLATE_*` |
| `app/webhook.py` | GET de verificação e POST com HMAC. Sem banco, avisa e usa memória |
| `app/hub/routes.py` | `GET /v1/hub/events`, `POST /v1/hub/migrate`, pairing, exchange do Embedded Signup |
| `app/hub/event_memory.py` | Fila em RAM, teto 5000, some se o processo do hub reiniciar. Vale para um worker só |
| `app/agent/routes.py` | Status, templates, envios, ticket e painel |
| `app/agent/send_service.py` | Upload do PDF, escolha sessão × modelo, grava `whatsapp_message` |
| `app/agent/schemas.py` | Corpo do `send-document`: `force_session`, `body_name`, `body_detail`, `envio_tipo` (padrão `boleto`) |
| `app/agent/poller.py` | A cada 10 s: `GET {hub}/v1/hub/events?since=&limit=100&waba_id=` com `X-PH-Hub-Secret` |
| `app/agent/phone.py` | Normalização do telefone |
| `app/agent/path_guard.py` | Recusa arquivo que não seja PDF dentro das pastas permitidas do PH |
| `app/agent/auth.py` | API key e ticket HMAC do painel |
| `app/db/repos.py` | Insert/update. Status não rebaixa `READ` nem `FAILED` |
| `app/db/migrate.py` | Aplica SQL. `schema_ok` olha se existe `public.whatsapp_webhook_event` |
| `app/graph/client.py` | Monta payload de documento e de template (header `document` com id de mídia) |
| `app/graph/templates.py` | Lista modelos (inclui `components`) |
| `app/crypto/tokens.py` | Token da Meta cifrado no banco |
| `sql/001_whatsapp_ph.sql` | `whatsapp_local_auth`, `whatsapp_config`, `whatsapp_message`, `whatsapp_webhook_event` |
| `sql/002_whatsapp_pairing.sql` | `whatsapp_pairing_blob` |
| `sql/003_whatsapp_poll_state.sql` | `whatsapp_poll_state` |
| `web/` | Painel Vite + React + Tailwind. Build em `web/dist` |
| `scripts/seed_dev_config.py` | Grava token/WABA/telefone de teste no Postgres local |
| `scripts/create_boleto_template.py` | Cria `ph_boleto_pdf` (upload resumível do PDF de exemplo) |
| `scripts/create_relatorio_template.py` | Cria `ph_relatorio_pdf` |
| `scripts/list_templates.py` | Lista modelos da WABA |
| `scripts/patch_relatorio_preview.py` | Patch CP1252 do C++ (tipo de envio + frase). Já aplicado |
| `scripts/patch_whatsmeta_utf8.py` | Patch CP1252 do `WhatsMetaClient.cpp` (UTF-8). Já aplicado. Se `Cp1252ToUtf8` existir, o script não reaplica |

Outros roteiros na pasta (`ROTEIRO_COMPLETO_...`, `docs/INTEGRACAO_PHVCL_WHATSMETA.md`, `docs/CHECKLIST_HUB_DIGITALOCEAN.md`) são anotações de fase. Em caso de conflito, valem o código e este arquivo.

---

## 6. Envio de PDF

`POST /v1/whatsapp/send-document` com `X-PH-Api-Key`. Corpo JSON em **UTF-8**.

Campos usados pelo GEPH:

| Campo | Boleto em grupo | Relatório avulso |
|-------|-----------------|------------------|
| `to` | `55` + telefone do cadastro | `55` + os 11 dígitos do diálogo |
| `file_path` | PDF temporário do Preview | PDF temporário do Preview |
| `caption` | texto já montado do boleto | “Relatório gerado no Sistema PH em anexo.” e, se houver, o nome do relatório |
| `body_name` | nome do cliente | título do relatório |
| `body_detail` | complemento do boleto | vazio |
| `envio_tipo` | `boleto` | `relatorio` |

`send_document` (`app/agent/send_service.py`):

1. Confere o PDF e sobe a mídia.
2. Se `envio_tipo` não for `boleto` nem `relatorio`, trata como boleto.
3. Consulta a WABA. Só usa o modelo se o status for `APPROVED` e o header for `DOCUMENT`.
4. Boleto: modelo `ph_boleto_pdf` / `pt_BR`. Variáveis `{{1}}` = nome, `{{2}}` = detalhe. Vazio vira `-` (a Meta recusa parâmetro vazio).
5. Relatório: modelo `ph_relatorio_pdf` / `pt_BR`. Só `{{1}}` = título (fallback `relatorio`). Corpo cadastrado, de propósito sem acento: `Relatorio gerado no Sistema PH: {{1}}. O PDF segue em anexo.`
6. Sem modelo aprovado: manda documento de sessão e devolve `warning` com o nome do modelo. O GEPH mostra esse aviso. A legenda da sessão do relatório **tem** acento; por isso o C++ precisa converter o JSON para UTF-8.
7. A resposta traz `delivery_mode` (`session` ou `template`) e `envio_tipo`.

Modelos criados em 24/09/2026 (ainda **PENDING** na última consulta daquele dia; não foram reconsultados em 25/09):

| Nome | Id | Header |
|------|-----|--------|
| `ph_boleto_pdf` | `1107643315105348` | DOCUMENT |
| `ph_relatorio_pdf` | `1768684757510601` | DOCUMENT |

`hello_world` e `3p_direct_integration_test_template` estão aprovados e **não** carregam PDF. Não usá-los no lugar dos dois acima.

Quando a Meta aprovar, o próximo envio já usa o modelo: a consulta é ao vivo, sem reiniciar o agente.

Prova do charset (24/09/2026): JSON com “Relatório” em CP1252 → HTTP 400 “There was an error parsing the body”. O mesmo JSON em UTF-8 → 400 “Apenas arquivos .pdf sao permitidos” (o corpo foi lido). O cliente C++ (`Cp1252ToUtf8` / `Utf8ToCp1252` em `WhatsMetaClient.cpp`) faz essa conversão. Sem Rebuild do `PH.bpl` e do GEPH, o executável em uso **não** tem essa correção nem o campo `envio_tipo`.

---

## 7. Entregue e Lido

A Meta **não** deixa consultar o status de um `wamid` (GET na Graph devolve 400). O único canal é o webhook do campo `messages`, objeto `statuses[]`.

Valores: `sent`, `delivered`, `read`, `failed`. Se o chat já estava aberto, a Meta pode mandar só `read` e omitir `delivered`. `read` implica entregue. Cada mensagem pode gerar até três avisos.

Cadeia no código:

1. Hub recebe o POST, confere o HMAC e grava o evento (ou a memória).
2. Poller do agente busca `since` = último id aplicado.
3. `update_message_status_by_meta_id` grava `SENT`, `DELIVERED`, `READ` ou `FAILED`.

Graus: `ACCEPTED` 1, `SENT` 2, `DELIVERED` 3, `READ` 4, `FAILED` 4. Um `sent` atrasado não apaga um `read`. `READ` e `FAILED` só aceitam o mesmo status de novo. Teste local em 24/09/2026 na linha `wamid.AUTOTEST.2`: `READ`→`SENT` alterou 0 linhas; `READ`→`READ` alterou 1; id inexistente alterou 0.

Rótulos do painel (`web/src/App.tsx`):

| Banco | Tela |
|-------|------|
| `ACCEPTED` | Aceito pela Meta |
| `SENT` | Enviado |
| `DELIVERED` | Entregue |
| `READ` | Lido |
| `FAILED` | Com falha |

O contador “Entregues” soma `DELIVERED` + `READ`. “Enviados” soma `SENT` + `ACCEPTED`.

As linhas `wamid.AUTOTEST.1` (`DELIVERED`) e `wamid.AUTOTEST.2` (`READ`) para `5549999999999` em 22/09/2026 são testes falsos. Não são leitura de PDF real.

Mensagens reais (incluindo o boleto das 17:48 de 24/09, id local 12) continuam `ACCEPTED`. A Meta não reenvia o recibo de uma mensagem antiga: aquela linha **não** vai virar Lido.

Por que o recibo real ainda não chega (25/09/2026):

1. O app está **não publicado**. O aviso amarelo do próprio painel da Meta diz que, nesse estado, só webhook de teste do painel é entregue. O botão Publicar está bloqueado: “Não foi possível publicar esse app porque nem todos os requisitos foram concluídos.”
2. Na tela Teste, `whatsapp_business_messaging` e `whatsapp_business_management` estão Concluídas. `public_profile` não. `business_management` ainda mostrava “0 de 1” às 11:45, embora `GET me/businesses` já tivesse devolvido o negócio. A tela diz que o visto pode levar até 24 horas e vale 30 dias.
3. O hub não persiste evento: `schema_ok: false`, `events_backend: memory`, `events_memory_count: 0`. `POST /v1/hub/migrate` falha com `permission denied for schema public`. O poller fica em `since=0` e não registra “Poller atualizou”.
4. POST no webhook **sem** assinatura responde 403 “Assinatura invalida”. O segredo do app está no hub. Não falta `META_APP_SECRET` lá. No `.env` **local** do agente esse segredo não está (e não precisa: quem valida o HMAC é o hub).

Não clicar em “Verificar e salvar” de novo: a URL e o campo `messages` já estão certos. Não adicionar as permissões `email`, `manage_app_solution` nem `whatsapp_business_manage_events`. Não clicar em “Torne-se um Provedor de Tecnologia”.

---

## 8. O que já está pronto

- Agente local sobe, conecta no Postgres `whatsapp_ph`, `schema_ok` verdadeiro, status `CONNECTED` depois do seed.
- Envio de PDF de boleto em grupo pela Cloud API. Em 24/09/2026, 17:48, o PDF do boleto 9 chegou no celular porque havia um “Oi” às 14:01 (janela de 24 h aberta). O GEPH mostrou o aviso de sessão, porque o modelo ainda era PENDING.
- Código de relatório avulso: `envio_tipo=relatorio`, frase padrão, aviso na tela.
- Código que troca para o modelo assim que ele estiver `APPROVED`.
- Conversão UTF-8 no cliente C++ (fonte; falta Rebuild).
- Atualização de status sem rebaixar leitura.
- App PH_Softwares inscrito na WABA.
- Webhook URL e campo `messages` assinados no painel da Meta.
- Painel React com ticket: lista, rótulos, contadores.
- HMAC do webhook rejeita POST anônimo (403).
- Dois modelos DOCUMENT criados na WABA (pendentes de aprovação humana da Meta).

## 9. O que falta

| Item | Quem resolve | Efeito enquanto falta |
|------|----------------|------------------------|
| Rebuild `PH.bpl` + GEPH no C++ Builder 5 | usuário, no IDE | O exe não manda `envio_tipo` nem JSON UTF-8. A frase com acento quebra o POST |
| Meta aprovar `ph_boleto_pdf` e `ph_relatorio_pdf` | Meta | Fora da janela de 24 h o PDF não é entregue. Dentro da janela segue a sessão + aviso |
| Publicar o app | usuário, quando a tela Teste e os requisitos liberarem o botão | Sem publicar, entrega/leitura de mensagem real não atualizam o painel |
| Visto de `business_management` (e `public_profile` se a Meta exigir) | esperar até 24 h após o teste de 25/09, ou repetir o teste no Graph Explorer | Botão Publicar continua bloqueado |
| Verificação da empresa | Meta (“em processamento”) | Pode ser requisito de publicação |
| Domínio `phsoftwares.com.br` | só se a verificação da empresa pedir | Sozinho não publica o app |
| Usuário Postgres do hub com `CREATE` em `public` | DigitalOcean / dono do banco | Eventos somem no reinício do hub; o poller não vê histórico |
| `META_EMBEDDED_SIGNUP_CONFIG_ID` | painel do app Meta | “Conectar” no GEPH continua bloqueado. O seed atual não depende disso |
| Copiar este código para a pasta do serviço e só então subir `PHWhatsMeta` | deploy | O serviço parado aponta para código velho em `D:\`. Subir os dois ao mesmo tempo briga pela porta 8767 |
| Commit/push do que mudou depois de `82218a6` | só se o usuário pedir | O GitHub não tem o `envio_tipo`, o rank de status nem os patches |

---

## 10. Como subir o agente neste PC

```powershell
cd C:\projetos\python\whatsmeta
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8767
```

O `python.exe` que aparece na linha de comando pode ser `C:\PHSFTW\PYTHON\python.exe`: é o interpretador base do venv (`pyvenv.cfg`), não uma cópia antiga do projeto. O que importa é o diretório de trabalho `C:\projetos\python\whatsmeta`.

Conferir:

```powershell
curl http://127.0.0.1:8767/health
```

Esperado: `"role":"agent"`, `"db_ok":true`, `"schema_ok":true`.

Não iniciar o serviço `PHWhatsMeta` enquanto esse processo estiver na 8767. Desde 19/10/2026 o serviço está rodando na 8767: para subir o venv deste repositório ao mesmo tempo, parar o serviço antes ou usar outra porta livre (a 8765 é do HUPH).

Variáveis que o `.env` do agente precisa ter (valores só no arquivo): `APP_ROLE=agent`, `DATABASE_URL`, `PH_API_KEY`, `TOKEN_ENCRYPTION_KEY`, `PANEL_TICKET_SECRET`, `HUB_BASE_URL`, `HUB_PULL_SECRET`, e as quatro chaves de modelo (`WHATSAPP_BOLETO_TEMPLATE_NAME=ph_boleto_pdf`, `WHATSAPP_BOLETO_TEMPLATE_LANG=pt_BR`, `WHATSAPP_RELATORIO_TEMPLATE_NAME=ph_relatorio_pdf`, `WHATSAPP_RELATORIO_TEMPLATE_LANG=pt_BR`). O token da conta em uso no dia a dia está cifrado em `whatsapp_config`, gravado pelo seed.

Editar `.env` em UTF-8. Não usar `Add-Content` do PowerShell (já corrompeu o arquivo uma vez).

---

## 11. Regras que não podem ser quebradas

- Fora das 24 horas, PDF livre não é entregue. Só modelo aprovado com header DOCUMENT.
- HTTP 200 e `wamid` não são entrega.
- Parâmetro de texto do modelo não pode ser string vazia.
- Variável de corpo não pode ser o primeiro nem o último caractere do modelo.
- O JSON que sai do C++ Builder tem de ser UTF-8. Os fontes `.cpp`/`.h`/`.dfm` continuam CP1252, sem BOM, CRLF. Não gravar esses fontes com o editor do agente em UTF-8; usar os scripts `patch_*.py` ou o C++ Builder.
- Não rebaixar status `READ` ou `FAILED`.
- Não commitar `.env`.
- Não tratar as linhas `AUTOTEST` como prova de que a leitura real funciona.
- Não esperar que o boleto já enviado (17:48, id 12) mude para Lido.

---

## 12. Onde continuar

Histórico da sessão no GEPH, com arquivos, bugs e validações: `C:\CBuilder5\Projects\GEPH\ajustesrealizados.md` seção 21.

Ordem prática quando o usuário voltar:

1. Rebuild do `PH.bpl` e do GEPH.
2. Olhar a tela Teste do app. Se `business_management` estiver Concluída, tentar Publicar.
3. Enviar um PDF **novo** (não reusar o das 17:48) e ver se o painel sai de Aceito pela Meta.
4. Se o webhook chegar e o hub reiniciar antes do poller, o evento se perde até existir tabela. Aí o passo é um usuário de banco com permissão de `CREATE` e `POST /v1/hub/migrate`.

---

## 13. Porta do agente: 8765 → 8767 (19/10/2026)

**Por quê.** O serviço HUPH (`C:\PHSFTW\SERVICOS\HUPH\huph.exe`) escuta em `127.0.0.1:8765` e passou a ser usado pela Central RTPH (eventos RTC no `ph_erp`). O usuário decidiu mudar a porta do WhatsApp, não a do HUPH, e escolheu 8767.

**O que mudou nesta máquina:**

- Serviço `PHWhatsMeta` (NSSM, início automático): `Application` `D:\PHSFTW\WHATSPH\.venv\Scripts\python.exe`, `AppDirectory` `D:\PHSFTW\WHATSPH`, `AppParameters` `-m uvicorn app.main:app --host 127.0.0.1 --port 8767`. Conferido em 19/10: Running, `GET /health` com `role=agent`, versão 0.2.4, `db_ok=true`, `schema_ok=true`.
- `PORT=8767` em `C:\PHSFTW\WHATSPH\.env` e `D:\PHSFTW\WHATSPH\.env`.
- Instalador, gravado em bytes (sem regravar o arquivo inteiro com editor UTF-8): `installer\install_service.bat`, `installer\first_run.py`, `installer\README_INSTALACAO.txt` (2 ocorrências), `installer\WHATSPH.iss` e `.env.example` deste repositório; as cópias `install_service.bat`, `first_run.py` e `README_INSTALACAO.txt` em `D:\PHSFTW\WHATSPH\`. Sem commit.
- Esta documentação, o `README.md`, `docs\INTEGRACAO_PHVCL_WHATSMETA.md` e os roteiros passaram a citar 8767.

**Cliente C++ (`Lib\phvcl\WhatsMetaClient.cpp` e `Lib\phvcl_nova\WhatsMetaClient.cpp`).** O construtor começa com `BaseUrl = "http://127.0.0.1:8765"`. `LoadFromWhatsPhEnv` troca a porta pela chave `PORT` do primeiro `.env` encontrado (`{PHSFTW}\WHATSPH\.env`, pastas acima, `C:\PHSFTW\WHATSPH\.env`, `D:\PHSFTW\WHATSPH\.env`). Por isso o GEPH não precisou ser recompilado: basta o `.env` ter `PORT=8767`. **Atenção:** se o `.env` não tiver `PORT`, o cliente fica no padrão 8765 e chama o HUPH, não o agente. Trocar esse padrão exige editar o `.cpp` (CP1252) e recompilar, o que não foi feito.

**Ainda com 8765 (não alterados):** `web\vite.config.ts` (proxy do `npm run dev`), `scripts\smoke_test.py` (URL padrão), scripts antigos `scripts\patch_*.py`, `scripts\reapply_geph_meta_warning.py`, `scripts\verify_final_review.py`, `scripts\write_whatsmeta_ui_cp1252.py`, o log `logs_agent_stderr.txt` e a pasta de build `dist\whatsph`. Para subir o agente em desenvolvimento ao lado do serviço, usar outra porta livre; 8765 é do HUPH e 8767 é do serviço.

---

## 14. `whatsph.exe` e serviço em `PHSFTW\SERVICOS\WHATSPH` (26/10/2026)

**Por quê.** O pedido foi seguir o modelo do HUPH (`C:\projetos\python\huph`): um único exe na pasta `PHSFTW\SERVICOS\<serviço>`, que roda o servidor e também instala e atualiza o próprio serviço do Windows. Antes, o agente era uma pasta com `.venv` + código solto, registrada pelo NSSM em `PHSFTW\WHATSPH` (instalador Inno `installer\WHATSPH.iss`).

**Como ficou.**

- `whatsph.exe` (PyInstaller, `whatsph.spec`, ícone `ph.ico`) leva dentro o Python, o código `app\`, `sql\` e `web\dist\` (painel). Versão **0.3.0**.
- Pasta de instalação: `<PHSFTW>\SERVICOS\WHATSPH\` com `whatsph.exe`, `.env` e `logs\`. O exe sempre lê o `.env` ao lado dele (`app\caminhos.py`).
- Serviço `PHWhatsMeta` registrado pelo próprio exe (pywin32, `app\servico_windows.py`), início automático, conta LocalSystem. O serviço roda `whatsph.exe run-server` como processo filho. Sem NSSM.
- O agente escuta sempre em `127.0.0.1`. Porta: `PORT` do `.env`; sem `PORT`, 8767.
- Logs: `logs\whatsph.log` (rotativo, 2 MB × 5) com tudo. `logs\whatsph-service.log` (sem rotação) só recebe erro fatal do processo filho: o log só vai para a tela quando o exe roda num console. A linha do `httpx` a cada consulta ao hub foi silenciada (nível WARNING).
- Se o agente cair, o serviço o reinicia (como o NSSM fazia): 5 s, dobrando até 60 s se cair logo após subir; volta a 5 s depois de 60 s rodando. Cada queda gera um Aviso no log de Aplicativo do Windows (`PHWhatsMeta: agente encerrou ...`). No stop, o agente é encerrado mesmo se o stop chegar durante um reinício.

**Comandos (`app\cli.py`).**

| Comando | Faz |
|---|---|
| `version` | Mostra a versão |
| `run-server` | Sobe o agente (é o que o serviço executa) |
| `verificar-servico [--timeout N]` | `GET /health` na porta do `.env`; código 0 se `status=ok` |
| `gerar-configuracao [--force]` | Cria o `.env` inicial (chaves novas); não sobrescreve sem `--force` |
| `aplicar-sql` | Aplica `sql\001..003` no `DATABASE_URL` (o startup já tenta) |
| `install-service`, `update-service`, `remove-service`, `start-service`, `stop-service`, `restart-service`, `debug-service` | Serviço `PHWhatsMeta` |

**Gerar o exe.** `.\scripts\build_exe.ps1` (instala `requirements-dev.txt`, roda o PyInstaller e mostra versão e SHA1). Saída: `dist\whatsph.exe`.

**Instalar ou atualizar (PowerShell como Administrador).**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\preparar_ambiente_whatsph.ps1 -ExecutavelOrigem <pasta>\whatsph.exe -Diretorio C:\PHSFTW\SERVICOS\WHATSPH
```

Sem `-Diretorio`, o destino é `<PHSFTW da origem>\SERVICOS\WHATSPH`. O script (modelo `preparar_ambiente_huph.ps1`): para o serviço, copia o exe, cria o `.env` se faltar, registra (`install-service`) ou atualiza (`update-service`), inicia e espera `/health` com `role=agent` e a versão do exe. Sucesso: JSON `WHATSPH_AMBIENTE_PRONTO`; falha: `WHATSPH_PREPARACAO_FALHA` com a etapa.

**Modo antigo (NSSM + Inno Setup) removido em 26/10/2026.** O usuário excluiu o serviço antigo (`sc delete`) e decidiu que ele não será usado em lugar nenhum. Saíram do repositório `installer\` (`WHATSPH.iss`, `install_service.bat`, `first_run.py`, `first_run.bat`, `apply_sql.bat`, `README_INSTALACAO.txt`) e `scripts\build_dist.ps1`; saíram também os builds locais `dist\installer\WHATSPH_Setup_0.2.4.exe` e `dist\whatsph\`. O `.env` inicial agora vem de `whatsph.exe gerar-configuracao` e o SQL de `whatsph.exe aplicar-sql` (o `scripts\apply_sql.py` de desenvolvimento continua). O `preparar_ambiente_whatsph.ps1` não migra mais NSSM: se o `PHWhatsMeta` estiver registrado com outro executável, recusa sem alterar nada. Ele mantém uma proteção: sem `.env` no destino, copia `<PHSFTW>\WHATSPH\.env` se existir, porque chaves novas quebrariam o GEPH (`PH_API_KEY`), a conta no banco (`INSTALLATION_ID`) e o token da Meta em `whatsapp_config` (`TOKEN_ENCRYPTION_KEY`). As pastas antigas `C:\PHSFTW\WHATSPH` e `D:\PHSFTW\WHATSPH` podem ser apagadas à mão depois do Rebuild do GEPH; **não** usar o `unins000.exe` delas (ele roda `nssm remove PHWhatsMeta` e removeria o serviço novo). A seção 13 cita arquivos do instalador que não existem mais: é histórico.

**GEPH (PHVCL, CP1252 por script; ajustado de novo em 26/10/2026 a pedido do usuário).** `TWhatsMetaClient::LoadFromWhatsPhEnv()` não recebe mais parâmetro e lê **um** arquivo: `<PHSFTW>\SERVICOS\WHATSPH\.env`, onde `<PHSFTW>` é a pasta `PHSFTW` encontrada subindo a partir da pasta do executável (`ExtractFilePath(Application->ExeName)`, mesmo ponto de partida do `Whats.exe`/`AssinadorPDF.exe`). Ex.: `C:\PHSFTW\GEPH\SISTEMA\GEPH.EXE` → `C:\PHSFTW\SERVICOS\WHATSPH\.env`. Padrão `C:\PHSFTW\SERVICOS\WHATSPH\.env` quando o caminho do executável não tem pasta `PHSFTW` ou quando o `.env` montado não existe (ex.: build em `E:\PHSFTW\Geph\SISTEMA`). Função auxiliar pública `TWhatsMetaClient::DiretorioWhatsPh()` (estática). Saíram as buscas antigas (`PHSFTW\WHATSPH`, `D:\PHSFTW`, varredura a partir de `vg.DiretorioPrincipal`). As 4 chamadas (`Preview.cpp` envio em grupo, `SenWA.cpp` envio avulso e verificação da conta, `WhatsMetaUi.cpp` `loadCli`) viraram uma chamada só. As mensagens de erro passaram a mostrar o caminho do `.env` (não encontrado, incompleto sem `PH_API_KEY` ou erro de leitura). Porta padrão do construtor 8767. Validação: patch com contagem exata; bytes acentuados 9→13 no `.cpp` (3 mensagens novas), demais arquivos iguais; sem BOM, CRLF, sem `EF BF BD`; `Application` vem de `forms.hpp` pelo `vcl.h`; lógica do caminho simulada com as regras do Delphi 5 (`ExtractFilePath`/`ExtractFileName`/`ExcludeTrailingBackslash`) em 10 caminhos, inclusive UNC, sem laço infinito. **Não compilado aqui:** vale depois do Rebuild do `PH.bpl` e do GEPH. O agente só escuta `127.0.0.1`: o GEPH precisa rodar na mesma máquina do serviço. GEPH aberto de unidade de rede (`X:\PHSFTW\...`) lê o `.env` da rede e chama o `127.0.0.1` da própria estação. Até o Rebuild, o `GEPH.EXE` atual continua lendo `C:\PHSFTW\WHATSPH\.env` (mesmas chaves); depois do Rebuild essa pasta deixa de ser lida.

**Testado em 26/10/2026 (sem tocar no serviço em uso).** Exe copiado para `%TEMP%\teste_whatsph\PHSFTW\SERVICOS\WHATSPH`: `version` 0.3.0; `gerar-configuracao` criou o `.env` com `PHSFTW_ROOT` da pasta PHSFTW de cima e, na 2ª vez, não sobrescreveu; `run-server` na porta 8799 respondeu `/health` (`role=agent`, 0.3.0); `/` serviu o painel React embutido e o `/assets/*.js` respondeu 200; `logs\whatsph.log` gravado. 
**Instalado nesta máquina em 26/10/2026 (autorizado pelo usuário).** Antes de rodar o script, o serviço `PHWhatsMeta` (NSSM) já não existia: o log de Aplicativo mostra `nssm` recebendo STOP às 13:40:04 e a chave `HKLM\SYSTEM\CurrentControlSet\Services\PHWhatsMeta` tinha sumido. O usuário confirmou que excluiu o serviço antigo à mão (`sc delete`): o modo NSSM não será mais usado em lugar nenhum, só o `whatsph.exe`. Como sem serviço o script trataria como 1ª instalação (e geraria chaves novas), o `.env` de `D:\PHSFTW\WHATSPH` foi copiado antes (hash igual) para `C:\PHSFTW\SERVICOS\WHATSPH\.env`. Resultado do script: `WHATSPH_AMBIENTE_PRONTO`, 0.3.0, `db_ok=true`. Conferido: serviço Running, Automatic, LocalSystem, `PathName` `"C:\PHSFTW\SERVICOS\WHATSPH\whatsph.exe"`; `/health` `role=agent`, `schema_ok=true`; `/v1/whatsapp/status` `CONNECTED`. 2ª execução do script: `atualizado` (caminho `update-service`). Sem `-Diretorio` e com o exe fora de um PHSFTW, o script recusa (igual ao HUPH). As pastas antigas `D:\PHSFTW\WHATSPH` e `C:\PHSFTW\WHATSPH` ficaram como estavam (o GEPH sem Rebuild ainda lê o `.env` delas).

**Ainda não feito.** Publicar `whatsph.exe` + `preparar_ambiente_whatsph.ps1` em `auxiliares` com `ListaHashs.txt` e atualização automática pelo BIPH (como o HUPH).

**Revisão de 26/10/2026 (mesmo dia).**

- Corrigido: tudo o que ia para `whatsph.log` era gravado também em `whatsph-service.log`, que não tem rotação. Agora o segundo fica parado (conferido: 2072 bytes antes e depois de 25 s de serviço).
- Acrescentado: reinício automático do agente (acima). Teste: processo `run-server` morto à força; voltou a responder em 7 s, Aviso no log do Windows.
- Corrigido no `preparar_ambiente_whatsph.ps1`: sem serviço registrado e sem `.env` no destino, o script gerava chaves novas mesmo com instalação antiga presente (foi o caso desta máquina). Agora procura antes o `.env` do `AppDirectory` do NSSM e depois `<PHSFTW do destino>\WHATSPH\.env`. Só gera um novo se nenhum existir. Se a instalação antiga estiver em outra unidade (ex.: `D:` com destino em `C:`), copiar o `.env` à mão antes.
- Acrescentado: se o script falhar depois de parar o serviço, tenta religá-lo (`servico_religado` no JSON).
- `verificar-servico`: `--timeout` inválido responde uso (código 2); a consulta ao `127.0.0.1` ignora proxy de ambiente.
- Conferido: `run-server` filho reaproveita a pasta de extração `_MEI` do processo do serviço (3 processos `whatsph.exe` no total). Stop do serviço: 0 processos, porta 8767 livre, pasta `C:\Windows\Temp\_MEI*` apagada. Start: volta a responder.
- Conferido: `C:\PHSFTW\WHATSPH\.env` (lido primeiro pelo GEPH sem Rebuild), `D:\PHSFTW\WHATSPH\.env` (serviço antigo) e `C:\PHSFTW\SERVICOS\WHATSPH\.env` têm os mesmos valores de `PH_API_KEY`, `INSTALLATION_ID`, `TOKEN_ENCRYPTION_KEY`, `PORT`, `DATABASE_URL`, `PHSFTW_ROOT`, `HUB_PULL_SECRET` e `PANEL_TICKET_SECRET` (comparados por hash, sem exibir).
- Teste funcional sem envio: `GET /v1/whatsapp/templates` pelo serviço novo (decifra o token e chama a Graph por HTTPS de dentro do exe). Resposta: `ph_boleto_pdf` e `ph_relatorio_pdf` **APPROVED** (pt_BR). As seções 3, 8 e 9 ainda dizem "pendente": os dois modelos estão aprovados.
- `Lib\phvcl_nova\WhatsMetaClient.cpp` (ramo `ramos/phvclnova`, r2258, versão antiga e diferente) **não** foi alterado: o GEPH compila com `Lib\phvcl` (`GEPH.bpr`). Continua com porta padrão 8765 e sem `SERVICOS\WHATSPH`.
- O `.env` desta máquina tem `APP_ENV=development` (veio do antigo): o `/docs` do FastAPI fica aberto no `127.0.0.1`. Não alterado.
