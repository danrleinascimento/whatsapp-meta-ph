# WhatsApp Meta PH — documentação do projeto

Documento para o próximo programador ou IA. Descreve o que o código faz, o que já está pronto, o que ainda falta e como ele se liga aos outros sistemas da PH Softwares.

Data desta descrição: **25/09/2026**.  
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
| `agent` | PC do escritório, só em `127.0.0.1:8765` | Enviar PDF e texto pela Graph API, gravar o envio no Postgres local, puxar os eventos do hub e servir o painel “Acompanhar envios”. |

O GEPH (C++ Builder 5) **não** fala com a Meta. Ele fala só com o agente local. O agente fala com a Graph API e com o hub. A Meta fala só com o hub (URL pública).

Nome interno do agente no escritório: **WHATSPH**. Serviço Windows previsto: `PHWhatsMeta` (NSSM). Nesta sessão o serviço estava **parado**. Quem atendia a porta 8765 era o uvicorn do venv deste repositório.

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
Agente local  127.0.0.1:8765  APP_ROLE=agent
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
| **Cópias de instalação** | `C:\PHSFTW\WHATSPH` e `D:\PHSFTW\WHATSPH` | `.env` recebeu as chaves dos modelos. O código em `D:\` **não** tem o `send_service.py` desta sessão. Não apontar o serviço NSSM para `D:\` enquanto o código novo não for copiado |
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
| Copiar este código para a pasta do serviço e só então subir `PHWhatsMeta` | deploy | O serviço parado aponta para código velho em `D:\`. Subir os dois ao mesmo tempo briga pela porta 8765 |
| Commit/push do que mudou depois de `82218a6` | só se o usuário pedir | O GitHub não tem o `envio_tipo`, o rank de status nem os patches |

---

## 10. Como subir o agente neste PC

```powershell
cd C:\projetos\python\whatsmeta
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

O `python.exe` que aparece na linha de comando pode ser `C:\PHSFTW\PYTHON\python.exe`: é o interpretador base do venv (`pyvenv.cfg`), não uma cópia antiga do projeto. O que importa é o diretório de trabalho `C:\projetos\python\whatsmeta`.

Conferir:

```powershell
curl http://127.0.0.1:8765/health
```

Esperado: `"role":"agent"`, `"db_ok":true`, `"schema_ok":true`.

Não iniciar o serviço `PHWhatsMeta` enquanto esse processo estiver na 8765.

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
