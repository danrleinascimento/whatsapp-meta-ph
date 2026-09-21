# PH Softwares --- Projeto de Integração WhatsApp Business Platform / Meta Cloud API

**Documento para desenvolvimento com Cursor/IA de programação**\
**Data da pesquisa:** 21/09/2026\
**Objetivo:** orientar a implementação completa da integração oficial do
WhatsApp no sistema legado da PH Softwares (C++ Builder 5) com um
serviço Python, incluindo onboarding dos escritórios clientes, envio de
textos e PDFs, Webhooks, segurança, logs, documentação do usuário e
testes.

------------------------------------------------------------------------

## 0. REGRA PRINCIPAL DESTE PROJETO

Este projeto deve utilizar **somente APIs oficiais da Meta/WhatsApp
Business Platform**.

Não utilizar:

-   WhatsApp Web automatizado;
-   Selenium/Playwright para controlar WhatsApp;
-   PyAutoGUI;
-   Baileys/Venom/UazAPI ou bibliotecas que imitem o cliente do
    WhatsApp;
-   engenharia reversa do protocolo;
-   tokens compartilhados entre clientes;
-   armazenamento de senhas da conta Meta do cliente;
-   qualquer mecanismo que dependa de uma sessão de navegador do
    WhatsApp.

A Meta mantém atualmente coleções oficiais de **Cloud API, Business
Management API e Embedded Signup**. A coleção oficial informa que
Embedded Signup é o fluxo destinado a Solution Partners, Tech Providers
e Tech Partners para onboarding de empresas clientes.

Fonte oficial:
https://www.postman.com/meta/whatsapp-business-platform/overview

------------------------------------------------------------------------

# 1. VISÃO DO PRODUTO

A PH Softwares possui um sistema contábil legado em C++ Builder 5
utilizado por centenas de escritórios.

Cada escritório deverá utilizar:

-   sua própria empresa/Business Portfolio da Meta;
-   seu próprio WhatsApp Business Account (WABA);
-   seu próprio número de telefone;
-   seu próprio perfil/nome comercial no WhatsApp;
-   seus próprios clientes/destinatários;
-   sua própria configuração de cobrança conforme o modelo de billing
    aplicável pela Meta.

A PH fornece o software e a integração.

Arquitetura desejada:

``` text
┌─────────────────────────────┐
│       SISTEMA PH            │
│       C++ Builder 5         │
│                             │
│ Clientes / Contabilidade    │
│ Geração de PDFs             │
│ Tela "Enviar WhatsApp"      │
└──────────────┬──────────────┘
               │ HTTPS/HTTP interno
               ▼
┌─────────────────────────────┐
│       SERVIÇO PH            │
│          PYTHON              │
│                             │
│ FastAPI/HTTP API            │
│ Meta Graph API client       │
│ OAuth/Embedded Signup       │
│ Media/PDF                   │
│ Templates                   │
│ Webhooks                    │
│ Logs/Auditoria              │
└──────────────┬──────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────┐
│        META                 │
│ WhatsApp Cloud API          │
│ Business Management API     │
│ Embedded Signup             │
└──────────────┬──────────────┘
               │
               ▼
        WhatsApp do cliente
```

------------------------------------------------------------------------

# 2. CORREÇÃO IMPORTANTE SOBRE O MODELO DE COBRANÇA

**Não assumir no código que cada escritório necessariamente receberá uma
fatura diretamente da Meta.**

A documentação oficial atual do Embedded Signup da Meta descreve um
fluxo em que empresas clientes podem solicitar acesso à **linha de
crédito do parceiro**; nesse modelo, o parceiro recebe uma fatura
agregada da Meta e cobra os clientes. A própria documentação diz que as
empresas pagam ao parceiro, que recebe a fatura agregada para pagar a
Meta.

Portanto, antes de implementar a tela definitiva de cobrança, a PH deve
confirmar com a Meta qual modelo de billing será aplicável ao
enquadramento da PH (Tech Provider/Tech Partner/Solution Partner) e aos
escritórios.

Isso é uma **decisão obrigatória de arquitetura e negócio**.

Fonte oficial:
https://www.postman.com/meta/whatsapp-business-platform/documentation/du6gzjv/embedded-signup

Fonte específica do fluxo de crédito:
https://www.postman.com/meta/whatsapp-business-platform/folder/kau55oi/step-3-share-line-of-credit-with-a-clients-waba

**Não programar uma afirmação como "o escritório paga diretamente a
Meta" até essa questão estar confirmada pela documentação/conta Meta da
PH.**

------------------------------------------------------------------------

# 3. DOCUMENTAÇÃO OFICIAL PRINCIPAL

## Meta / WhatsApp Business Platform

### Central/coleções oficiais da Meta no Postman

https://www.postman.com/meta/whatsapp-business-platform/overview

### Cloud API

https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api

### Mensagens

https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ba8d099d-007e-4b52-b9f2-3cf3c60e4fbc

### Media

https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ecb27be5-4d27-4763-bbee-6a8002c04bf3

### Embedded Signup

https://www.postman.com/meta/whatsapp-business-platform/documentation/du6gzjv/embedded-signup

### Business Management API

https://www.postman.com/meta/whatsapp-business-platform/overview

### Política do WhatsApp Business

https://business.whatsapp.com/policy/preview?lang=pt_BR

### Preços

Usar sempre a página oficial vigente da Meta:
https://business.whatsapp.com/products/platform-pricing/

**Regra para a Cursor:** preços, versões da Graph API, permissões,
limites e requisitos devem ser consultados novamente na documentação
oficial antes de codificar. Não usar blogs como fonte primária para
decisões da implementação.

------------------------------------------------------------------------

# 4. CONCEITO DOS PRINCIPAIS OBJETOS

A equipe deve compreender a diferença:

## Business Portfolio

É a estrutura empresarial na Meta que administra ativos comerciais.

## WABA

WhatsApp Business Account.

É a conta empresarial do WhatsApp que contém os ativos do WhatsApp
Business Platform.

## Phone Number ID

É o identificador interno do número utilizado pela Cloud API.

O endpoint de mensagens utiliza o Phone Number ID:

``` text
POST https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages
```

## Access Token

Credencial utilizada pelo servidor para autenticar chamadas à Graph API.

**Nunca colocar token no código-fonte do C++ Builder.**

## App ID / App Secret

Credenciais do aplicativo Meta criado pela PH.

O App Secret também deve permanecer somente no servidor.

## Message ID

Identificador retornado pela API para uma mensagem enviada.

Deve ser gravado para posterior correlação com Webhooks.

------------------------------------------------------------------------

# 5. MODELO MULTIEMPRESA DA PH

A PH deve ser tratada como plataforma que atende várias empresas.

Cada escritório deve ter uma configuração independente.

Exemplo:

``` text
PH Softwares
│
├── Escritório A
│   ├── Business ID A
│   ├── WABA ID A
│   ├── Phone Number ID A
│   └── credenciais/estado A
│
├── Escritório B
│   ├── Business ID B
│   ├── WABA ID B
│   ├── Phone Number ID B
│   └── credenciais/estado B
│
└── Escritório C
    ├── Business ID C
    ├── WABA ID C
    ├── Phone Number ID C
    └── credenciais/estado C
```

Nunca misturar os ativos de uma empresa com outra.

No banco, todas as operações WhatsApp devem possuir uma chave de
empresa/escritório.

------------------------------------------------------------------------

# 6. EMBEDDED SIGNUP --- FLUXO QUE DEVE SER ESTUDADO PRIMEIRO

O Embedded Signup é o mecanismo oficial da Meta para onboarding de
empresas clientes por Solution Partners, Tech Providers e Tech Partners.

A documentação oficial informa que:

1.  O app da PH precisa passar por App Review.
2.  É necessário solicitar Advanced Access para permissões como:
    -   `business_management`
    -   `whatsapp_business_management`
3.  O fluxo é incorporado em um site/portal usando Facebook JavaScript
    SDK e Facebook Login.
4.  Depois do onboarding, a integração precisa buscar/confirmar os WABAs
    compartilhados.
5.  Deve adicionar o System User à WABA conforme o modelo da Meta.
6.  Deve registrar o número.
7.  Deve configurar Webhooks.
8.  Templates aprovados podem ser consultados pela API.

Fonte:
https://www.postman.com/meta/whatsapp-business-platform/documentation/du6gzjv/embedded-signup

------------------------------------------------------------------------

# 7. ATENÇÃO: O C++ BUILDER 5 NÃO DEVE EXECUTAR O EMBEDDED SIGNUP

O fluxo de autorização deve ser tratado como experiência web.

Arquitetura recomendada:

``` text
C++ Builder
   │
   │ abre URL HTTPS
   ▼
Portal/Web da PH
   │
   ▼
Meta Embedded Signup
   │
   ▼
Usuário faz login e autoriza
   │
   ▼
Callback/backend PH
   │
   ▼
Python salva/valida configuração
   │
   ▼
C++ recebe somente estado/resumo
```

O Cursor deve avaliar a melhor forma de abrir o fluxo a partir do
desktop:

-   navegador padrão;
-   página web segura;
-   callback controlado;
-   polling de status;
-   ou outra técnica oficialmente suportada.

Não colocar App Secret ou credenciais administrativas dentro do
executável C++.

------------------------------------------------------------------------

# 8. REQUISITOS DA CONTA DA PH

Antes do desenvolvimento completo:

1.  Criar/confirmar Business Portfolio da PH.
2.  Criar o aplicativo Meta.
3.  Adicionar os produtos necessários.
4.  Configurar WhatsApp.
5.  Configurar Facebook Login for Business conforme exigido pelo
    Embedded Signup.
6.  Configurar domínio/URLs HTTPS.
7.  Configurar Webhooks.
8.  Configurar App Review.
9.  Solicitar Advanced Access das permissões necessárias.
10. Configurar usuários/sistema administrativo.
11. Definir modelo de billing.
12. Criar ambiente de teste.

**O Cursor não deve inventar nomes de telas da Meta. A interface da Meta
pode mudar. Sempre confirmar a nomenclatura atual na documentação
oficial.**

------------------------------------------------------------------------

# 9. PERMISSÕES

A coleção oficial da Cloud API informa como permissões principais:

``` text
whatsapp_business_management
whatsapp_business_messaging
```

Para alguns recursos administrativos/Business Portfolio podem existir
permissões adicionais.

Fonte:
https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api

O Cursor deve:

-   solicitar somente permissões necessárias;
-   separar permissões de desenvolvimento e produção;
-   não colocar permissões desnecessárias;
-   documentar o motivo de cada permissão;
-   validar as permissões efetivamente concedidas pelo token.

------------------------------------------------------------------------

# 10. TOKENS E SEGURANÇA

O token de teste de usuário pode ter validade curta.

A documentação oficial informa que tokens de usuário podem expirar
rapidamente e recomenda System User Access Token para operação de
servidor quando aplicável.

Fonte:
https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api

Regras:

-   nunca salvar token em `.cpp`;
-   nunca salvar token no executável;
-   nunca salvar App Secret no C++;
-   nunca registrar token em log;
-   nunca retornar token em JSON para o C++;
-   nunca mostrar token na interface do usuário;
-   criptografar credenciais persistidas;
-   controlar acesso ao banco;
-   usar HTTPS;
-   rotacionar/revogar credenciais quando necessário.

A Cursor deve estudar a melhor forma de armazenamento de secrets no
ambiente Windows onde o serviço Python será executado.

------------------------------------------------------------------------

# 11. BANCO DE DADOS --- MODELO INICIAL

A implementação deve adaptar os nomes ao padrão já existente no banco da
PH.

Sugestão lógica:

## whatsapp_config

``` text
id
empresa_id
business_id
waba_id
phone_number_id
display_phone_number
verified_name
status
token_reference
token_encrypted
token_created_at
token_expires_at
connected_at
disconnected_at
last_validation_at
created_at
updated_at
```

Se o token não puder/ não precisar ser persistido dessa forma conforme o
fluxo oficial, usar a estratégia de credencial recomendada pela Meta.

## whatsapp_message

``` text
id
empresa_id
phone_number_id
cliente_id
recipient_phone
message_type
template_name
template_language
media_id
filename
message_id
status
error_code
error_message
created_at
sent_at
delivered_at
read_at
failed_at
```

## whatsapp_webhook_event

``` text
id
empresa_id
waba_id
phone_number_id
event_type
message_id
payload
received_at
processed_at
processing_status
error
```

O payload original pode ser armazenado somente se houver necessidade
operacional/legal e respeitando a política de retenção da PH.

------------------------------------------------------------------------

# 12. SERVIÇO PYTHON

O serviço Python será a camada de integração.

Responsabilidades:

-   autenticação;
-   chamadas Graph API;
-   Embedded Signup/callback;
-   validação das configurações;
-   envio de texto;
-   upload de PDF;
-   envio de documento;
-   envio de templates;
-   Webhooks;
-   logs;
-   retry controlado;
-   tratamento de erros;
-   auditoria;
-   isolamento por empresa.

### Stack sugerida para avaliação

O Cursor deve avaliar e justificar:

``` text
Python 3.12 ou versão suportada oficialmente pelo ambiente
FastAPI
Uvicorn
httpx
Pydantic
SQLAlchemy ou acesso ao banco já padronizado pela PH
cryptography
```

Não adicionar bibliotecas desnecessárias.

Para chamadas HTTP, preferir cliente moderno e explícito, como `httpx`,
ou outra biblioteca que a Cursor considere tecnicamente superior após
verificar compatibilidade.

------------------------------------------------------------------------

# 13. ESTRUTURA SUGERIDA DO PROJETO PYTHON

``` text
ph_whatsapp/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── health.py
│   │   ├── whatsapp.py
│   │   ├── onboarding.py
│   │   └── webhook.py
│   │
│   ├── services/
│   │   ├── meta_graph.py
│   │   ├── whatsapp_service.py
│   │   ├── media_service.py
│   │   ├── template_service.py
│   │   ├── onboarding_service.py
│   │   └── webhook_service.py
│   │
│   ├── repositories/
│   │   ├── whatsapp.py
│   │   └── messages.py
│   │
│   ├── models/
│   │   ├── whatsapp.py
│   │   └── messages.py
│   │
│   └── security/
│       ├── tokens.py
│       └── encryption.py
│
├── tests/
├── migrations/
├── requirements.txt
├── .env.example
├── README.md
└── pyproject.toml
```

A estrutura é uma proposta inicial. O Cursor deve adaptá-la ao padrão de
projetos Python já existente na PH.

------------------------------------------------------------------------

# 14. CONFIGURAÇÃO

Não colocar segredos diretamente no código.

Exemplo conceitual:

``` env
META_APP_ID=
META_APP_SECRET=
META_GRAPH_VERSION=
META_WEBHOOK_VERIFY_TOKEN=
META_WEBHOOK_APP_SECRET=
DATABASE_URL=
```

Segredos de produção devem ficar em armazenamento seguro do servidor,
não no repositório Git.

`.env` pode existir somente em desenvolvimento local.

------------------------------------------------------------------------

# 15. CLIENTE DA GRAPH API

Criar uma camada única para chamadas Meta.

Exemplo conceitual:

``` python
class MetaGraphClient:
    async def get(...):
        ...

    async def post(...):
        ...

    async def delete(...):
        ...
```

Essa camada deve:

-   montar URL corretamente;
-   enviar Authorization;
-   configurar timeout;
-   interpretar HTTP status;
-   interpretar JSON;
-   preservar código/ID de erro da Meta;
-   não expor token;
-   registrar request ID quando disponível;
-   permitir retry somente quando seguro.

Não espalhar chamadas `httpx.post()` pela aplicação inteira.

------------------------------------------------------------------------

# 16. ENVIO DE TEXTO

Endpoint oficial:

``` text
POST https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages
```

A coleção oficial de mensagens informa que `/messages` é utilizado para
texto, mídia e templates.

Fonte:
https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ba8d099d-007e-4b52-b9f2-3cf3c60e4fbc

Payload conceitual:

``` json
{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "55XXXXXXXXXXX",
  "type": "text",
  "text": {
    "body": "Olá! Esta é uma mensagem enviada pelo sistema PH."
  }
}
```

A Cursor deve confirmar a versão atual da Graph API e o schema vigente
antes de implementar.

------------------------------------------------------------------------

# 17. ENVIO DE PDF

A Cloud API possui endpoints oficiais de mídia.

A coleção oficial informa:

``` text
POST /{phone-number-ID}/media
GET  /{media-ID}
DELETE /{media-ID}
GET  /{media-URL}
```

Fonte:
https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ecb27be5-4d27-4763-bbee-6a8002c04bf3

Fluxo recomendado:

``` text
PDF local
   │
   ▼
Python
   │
   ▼
POST /PHONE_NUMBER_ID/media
   │
   ▼
media_id
   │
   ▼
POST /PHONE_NUMBER_ID/messages
   │
   ▼
type=document
   │
   ▼
WhatsApp
```

O serviço deve:

-   verificar se o arquivo existe;
-   verificar extensão/MIME;
-   verificar tamanho;
-   impedir caminhos arbitrários;
-   não confiar no nome do arquivo enviado pelo cliente;
-   gerar nome seguro;
-   controlar arquivos temporários;
-   remover temporários após processamento;
-   registrar `media_id` e `message_id`.

------------------------------------------------------------------------

# 18. ENVIO DE DOCUMENTO

O payload deve seguir a documentação atual da Meta.

Conceito:

``` json
{
  "messaging_product": "whatsapp",
  "to": "55XXXXXXXXXXX",
  "type": "document",
  "document": {
    "id": "MEDIA_ID",
    "caption": "Segue seu documento.",
    "filename": "documento.pdf"
  }
}
```

A Cursor deve confirmar na documentação atual:

-   campos obrigatórios;
-   tipos MIME;
-   limite de tamanho;
-   comportamento de mídia;
-   tempo de disponibilidade;
-   erros;
-   política de retenção.

------------------------------------------------------------------------

# 19. TEMPLATES

A política oficial do WhatsApp Business informa que a empresa só pode
iniciar conversas usando **modelo de mensagem aprovado**.

Também informa que uma empresa pode responder sem template dentro da
janela de 24 horas após a última mensagem do usuário, observadas as
regras aplicáveis.

Fonte: https://business.whatsapp.com/policy/preview?lang=pt_BR

Portanto o sistema deve distinguir:

``` text
MENSAGEM DE RESPOSTA
```

de:

``` text
MENSAGEM INICIADA PELA EMPRESA
```

Não permitir que o usuário do sistema simplesmente digite qualquer
mensagem e o sistema envie indiscriminadamente fora da janela permitida.

------------------------------------------------------------------------

# 20. TEMPLATES DO SISTEMA PH

Avaliar a possibilidade de fornecer templates aprovados por cada WABA.

Exemplos de uso:

### Documento disponível

``` text
Olá {{1}}!

O documento referente à competência {{2}}
está disponível.

Empresa: {{3}}
```

### Boleto

``` text
Olá {{1}}!

O boleto referente à competência {{2}}
está disponível.

Vencimento: {{3}}.
```

### Aviso

``` text
Olá {{1}}!

A documentação da competência {{2}}
está disponível no sistema PH.
```

**Não assumir categoria do template sem confirmar as categorias atuais
da Meta.**

O Embedded Signup oficial mostra endpoint para consultar
`message_templates` da WABA do cliente.

------------------------------------------------------------------------

# 21. WEBHOOKS

Implementar Webhook HTTPS.

Objetivos:

-   receber confirmação de mensagens;
-   receber eventos de status;
-   receber mensagens recebidas;
-   correlacionar `message_id`;
-   registrar erros;
-   atualizar banco.

A documentação oficial mostra que a aplicação precisa estar inscrita na
WABA para receber eventos dos números associados.

Endpoint conceitual:

``` text
POST /webhook/whatsapp
```

E endpoint de verificação conforme o protocolo exigido pela Meta.

A coleção oficial mostra:

``` text
POST /{WABA-ID}/subscribed_apps
```

para assinar o app à WABA.

Fonte:
https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api

------------------------------------------------------------------------

# 22. WEBHOOK --- SEGURANÇA

Implementar:

-   HTTPS obrigatório;
-   verificação do token de validação;
-   validação da assinatura conforme documentação atual;
-   proteção contra replay quando aplicável;
-   idempotência;
-   logs;
-   resposta rápida ao webhook;
-   processamento assíncrono quando necessário.

Não fazer processamento pesado diretamente na requisição do webhook.

------------------------------------------------------------------------

# 23. IDEMPOTÊNCIA

Webhooks podem ser repetidos.

O sistema deve conseguir receber o mesmo evento mais de uma vez sem:

-   duplicar mensagem;
-   duplicar atualização;
-   criar duas cobranças;
-   executar duas vezes uma ação.

Criar chave única baseada nos identificadores fornecidos pela Meta
quando aplicável.

------------------------------------------------------------------------

# 24. API DO PYTHON PARA O C++ BUILDER

Criar endpoints internos, por exemplo:

``` text
GET  /health
GET  /whatsapp/status/{empresa_id}
POST /whatsapp/connect/start
POST /whatsapp/send-text
POST /whatsapp/send-pdf
GET  /whatsapp/message/{id}
POST /webhook/whatsapp
```

Os nomes são apenas proposta e devem ser ajustados.

------------------------------------------------------------------------

# 25. AUTENTICAÇÃO ENTRE C++ E PYTHON

Não deixar a API Python aberta para qualquer computador.

Avaliar:

-   HTTPS;
-   API key por instalação;
-   autenticação mútua;
-   JWT;
-   rede privada/VPN;
-   allowlist;
-   assinatura das requisições.

A solução deve considerar que o C++ Builder 5 é um cliente legado e não
deve possuir os segredos da Meta.

------------------------------------------------------------------------

# 26. INTEGRAÇÃO NO C++ BUILDER 5

Criar uma camada isolada, por exemplo:

``` text
WhatsAppService.cpp
WhatsAppService.h
```

Responsabilidades:

``` text
Conectar WhatsApp
Verificar status
Enviar texto
Enviar PDF
Consultar status
Abrir tela/configuração
```

Não colocar código da Graph API diretamente nos formulários.

Exemplo conceitual:

``` cpp
bool EnviarWhatsAppTexto(
    int EmpresaID,
    const String& Telefone,
    const String& Mensagem
);
```

e:

``` cpp
bool EnviarWhatsAppPDF(
    int EmpresaID,
    const String& Telefone,
    const String& ArquivoPDF,
    const String& Mensagem
);
```

A implementação real deve respeitar as bibliotecas HTTP/JSON já
existentes no projeto PH.

------------------------------------------------------------------------

# 27. NÃO ALTERAR DESNECESSARIAMENTE O LEGADO

A Cursor deve:

1.  estudar o código existente;
2.  identificar padrões atuais;
3.  identificar biblioteca HTTP já utilizada;
4.  identificar biblioteca JSON já utilizada;
5.  identificar padrão de acesso ao banco;
6.  criar uma camada nova e isolada;
7.  evitar alterar unidades antigas sem necessidade;
8.  manter compatibilidade com C++ Builder 5;
9.  compilar o projeto completo após cada etapa.

------------------------------------------------------------------------

# 28. TELA DO SISTEMA PH

Criar uma tela de configuração simples.

Exemplo:

``` text
WHATSAPP

Status:
[ 🟢 CONECTADO ]

Número:
(49) 99999-9999

Empresa:
ABC Contabilidade

Conta WhatsApp:
Conectada

Última validação:
21/09/2026 09:00

[ CONECTAR WHATSAPP ]
[ TESTAR CONEXÃO ]
[ DESCONECTAR ]
```

Não mostrar tokens.

------------------------------------------------------------------------

# 29. PRIMEIRO PASSO DE USO PELO ESCRITÓRIO

Fluxo do usuário:

``` text
1. Abrir sistema PH
2. Acessar Configurações
3. WhatsApp
4. Clicar "Conectar WhatsApp"
5. Abrir fluxo oficial Meta
6. Login/autorização
7. Selecionar/criar Business Portfolio conforme permitido
8. Configurar WhatsApp Business
9. Selecionar/configurar número
10. Confirmar/verificar número
11. Autorizar PH
12. Retornar ao sistema
13. PH valida a conexão
14. Sistema mostra "WhatsApp conectado"
```

A interface deve refletir exatamente o fluxo vigente da Meta.

------------------------------------------------------------------------

# 30. MANUAL DO USUÁRIO --- O QUE A PH DEVE ESCREVER

Criar manual com:

## Antes de começar

-   possuir conta Meta adequada;
-   possuir empresa/business portfolio;
-   possuir número de telefone elegível;
-   ter acesso administrativo;
-   ter telefone disponível para verificação;
-   entender que o número será utilizado pela plataforma oficial.

## Durante a conexão

Explicar cada tela sem reproduzir telas da Meta desatualizadas.

## Depois

Mostrar:

``` text
WhatsApp conectado ✓
```

## Teste

Enviar uma mensagem de teste para um número autorizado/controlado pelo
próprio escritório.

------------------------------------------------------------------------

# 31. NÚMERO DE TELEFONE

A Cursor deve pesquisar na documentação atual da Meta:

-   requisitos de número;
-   possibilidade de usar número já utilizado pelo WhatsApp/WhatsApp
    Business;
-   coexistência, se disponível para o caso;
-   migração;
-   verificação;
-   PIN;
-   limites;
-   regras específicas de números já cadastrados.

**Não inventar comportamento.**

Se houver conflito entre documentação antiga e nova, priorizar a
documentação mais recente da Meta.

------------------------------------------------------------------------

# 32. TESTE INICIAL

Antes de integrar ao C++:

### Teste 1

Python → Meta → mensagem de texto.

### Teste 2

Python → Meta → PDF.

### Teste 3

Meta → Webhook → Python.

### Teste 4

Python → banco → status.

### Teste 5

C++ → Python → Meta → texto.

### Teste 6

C++ → Python → Meta → PDF.

### Teste 7

Escritório A e Escritório B simultaneamente, garantindo isolamento.

------------------------------------------------------------------------

# 33. TESTE MULTIEMPRESA

Obrigatório.

Criar pelo menos:

``` text
Empresa A
Phone Number ID A

Empresa B
Phone Number ID B
```

Enviar:

``` text
Empresa A → Cliente A
Empresa B → Cliente B
```

Confirmar que:

-   A nunca usa o número B;
-   B nunca usa o número A;
-   tokens não são compartilhados;
-   logs estão separados;
-   templates são associados à WABA correta;
-   Webhooks conseguem identificar a empresa correta.

------------------------------------------------------------------------

# 34. TRATAMENTO DE ERROS

O sistema deve diferenciar:

``` text
Erro de configuração
Erro de autenticação
Token expirado
Número não registrado
Número inválido
Destinatário inválido
Template não aprovado
Template pausado
Limite da API
Erro temporário da Meta
Arquivo inválido
PDF grande demais
Timeout
Erro de rede
Webhook inválido
```

A interface do C++ deve mostrar mensagem amigável.

Exemplo:

``` text
Não foi possível enviar a mensagem.

Motivo:
A configuração do WhatsApp deste escritório precisa
ser reconectada.

Código técnico: XXXXX
```

O log técnico pode guardar mais detalhes.

------------------------------------------------------------------------

# 35. RETRY

Não repetir automaticamente qualquer erro.

Retry somente em erros transitórios e quando a operação for segura.

Criar:

-   limite de tentativas;
-   backoff;
-   timeout;
-   registro da tentativa;
-   correlação por message/request ID.

Erros de configuração/autorização devem ser apresentados ao usuário, não
ficar em loop.

------------------------------------------------------------------------

# 36. FILA DE ENVIO

Para produção, avaliar fila.

Exemplo:

``` text
C++ solicita envio
       ↓
Python grava tarefa
       ↓
Fila
       ↓
Worker
       ↓
Meta
       ↓
Resultado
       ↓
Banco
```

Isso evita travar o sistema contábil durante grandes lotes.

A tecnologia da fila deve ser escolhida depois de analisar o volume real
da PH.

Para uma primeira versão, pode existir envio síncrono; para produção em
escala, avaliar worker/fila.

------------------------------------------------------------------------

# 37. ENVIO DE MUITOS CLIENTES

Não implementar um loop simples:

``` python
for cliente in clientes:
    enviar()
```

sem controle.

Para lotes:

-   fila;
-   controle de velocidade;
-   retry;
-   status;
-   cancelamento;
-   progresso;
-   erros individuais;
-   prevenção de duplicidade;
-   limites da Meta;
-   janela de mensagens;
-   templates.

------------------------------------------------------------------------

# 38. LOG DE AUDITORIA

Registrar pelo menos:

``` text
empresa_id
usuário_ph
cliente_id
telefone
tipo
template
arquivo
message_id
data/hora
status
erro
```

Não registrar:

-   Access Token;
-   App Secret;
-   senha da Meta;
-   dados secretos.

------------------------------------------------------------------------

# 39. PRIVACIDADE

Como o sistema contábil trabalha com documentos potencialmente
sensíveis:

-   usar HTTPS;
-   restringir acesso;
-   proteger PDFs temporários;
-   apagar arquivos temporários;
-   controlar logs;
-   limitar acesso administrativo;
-   avaliar retenção de mensagens;
-   avaliar LGPD;
-   documentar responsabilidade entre PH e escritório;
-   não armazenar dados além do necessário.

A política oficial do WhatsApp Business estabelece responsabilidades do
negócio sobre suas interações e dados.

Fonte: https://business.whatsapp.com/policy/preview?lang=pt_BR

------------------------------------------------------------------------

# 40. PDF E SEGURANÇA

Nunca aceitar um caminho de arquivo arbitrário enviado por uma
requisição externa.

O serviço deve:

1.  receber uma referência segura;
2.  validar que o arquivo pertence à empresa;
3.  validar extensão;
4.  validar MIME;
5.  validar tamanho;
6.  evitar path traversal;
7.  gerar nome seguro;
8.  enviar;
9.  apagar temporário.

------------------------------------------------------------------------

# 41. CREDENCIAIS POR EMPRESA

Nunca usar:

``` text
TOKEN_GLOBAL
```

para todos os escritórios se a arquitetura oficial exigir
credenciais/ativos separados.

O serviço precisa identificar:

``` text
empresa_id
      ↓
configuração WhatsApp
      ↓
WABA
      ↓
Phone Number ID
      ↓
credencial autorizada
```

------------------------------------------------------------------------

# 42. DESCONECTAR WHATSAPP

Criar função:

``` text
Desconectar WhatsApp
```

Ela deve:

-   revogar/remover associação conforme APIs suportadas;
-   apagar ou invalidar credenciais locais;
-   manter histórico de mensagens;
-   mudar status para desconectado;
-   impedir novos envios;
-   orientar o usuário sobre como reconectar.

Não apagar histórico contábil.

------------------------------------------------------------------------

# 43. RECONEXÃO

Criar fluxo:

``` text
WhatsApp desconectado
        ↓
[Reconectar]
        ↓
Embedded Signup
        ↓
Meta
        ↓
Nova autorização
        ↓
Validar
        ↓
Conectado
```

------------------------------------------------------------------------

# 44. MONITORAMENTO

Criar endpoint:

``` text
GET /health
```

Retornar somente informações não sensíveis.

Exemplo:

``` json
{
  "status": "ok",
  "service": "ph-whatsapp",
  "version": "1.0.0"
}
```

Para diagnóstico, criar endpoint administrativo separado.

------------------------------------------------------------------------

# 45. DOCUMENTAÇÃO PARA DESENVOLVEDORES

O projeto Python deve conter:

``` text
README.md
ARCHITECTURE.md
SECURITY.md
DEPLOYMENT.md
WEBHOOKS.md
META_SETUP.md
TROUBLESHOOTING.md
```

O projeto C++ deve ter documentação equivalente.

------------------------------------------------------------------------

# 46. CONTROLE DE VERSÃO DA GRAPH API

Nunca deixar:

``` text
vXX.X
```

espalhado pelo código.

Criar configuração central:

``` text
META_GRAPH_VERSION
```

A Cursor deve verificar a versão vigente na data da implementação e
criar estratégia para atualização futura.

------------------------------------------------------------------------

# 47. POSTMAN PARA DESENVOLVIMENTO

Usar a coleção oficial da Meta no Postman para validar manualmente:

-   token;
-   WABA;
-   Phone Number ID;
-   envio de texto;
-   envio de documento;
-   templates;
-   Webhook;
-   permissões.

Fonte: https://www.postman.com/meta/whatsapp-business-platform/overview

A implementação Python somente deve ser considerada correta depois que
os mesmos fluxos forem entendidos/validados na coleção oficial.

------------------------------------------------------------------------

# 48. FLUXO COMPLETO DO ENVIO

``` text
Usuário C++
   │
   │ Enviar PDF
   ▼
C++ Builder
   │
   │ POST para Python
   ▼
Python API
   │
   ├── valida empresa
   ├── valida WhatsApp
   ├── valida telefone
   ├── valida PDF
   │
   ▼
Meta Graph API
   │
   ├── upload media
   │
   ▼
media_id
   │
   ▼
/messages
   │
   ▼
message_id
   │
   ▼
Python
   │
   ▼
Banco PH
   │
   ▼
C++ recebe resultado
```

Depois:

``` text
Meta
   │
   ▼
Webhook
   │
   ▼
Python
   │
   ▼
Atualiza status
   │
   ▼
Banco
```

------------------------------------------------------------------------

# 49. RESULTADO ESPERADO NO C++

Exemplo:

``` text
WhatsApp

Cliente: João da Silva
Telefone: (49) 99999-9999

Mensagem:
Olá João, segue seu documento.

Arquivo:
BOLETO_09_2026.pdf

[ ENVIAR ]
```

Resultado:

``` text
✓ Mensagem enviada
ID: wamid....
```

Se falhar:

``` text
✗ Não foi possível enviar

Motivo:
Template não aprovado / WhatsApp desconectado /
telefone inválido / erro temporário etc.
```

------------------------------------------------------------------------

# 50. STATUS DE MENSAGEM

Criar estados internos, por exemplo:

``` text
PENDING
SENDING
SENT
DELIVERED
READ
FAILED
CANCELED
```

Mapear cuidadosamente para os estados efetivamente enviados pela Meta.

Não assumir que todos os estados internos possuem correspondência 1:1.

------------------------------------------------------------------------

# 51. RESPONSABILIDADE DO ESCRITÓRIO

No manual do usuário, deixar claro:

O escritório é responsável por:

-   possuir uma conta empresarial adequada;
-   manter seus dados atualizados;
-   possuir/administrar o número;
-   autorizar a integração;
-   utilizar o WhatsApp conforme as políticas;
-   manter templates/conteúdos adequados;
-   possuir base legal/consentimento quando necessário;
-   acompanhar sua situação de cobrança conforme o modelo vigente.

A PH é responsável pela integração de software.

------------------------------------------------------------------------

# 52. RESPONSABILIDADE DA PH

A PH deve:

-   proteger credenciais;
-   manter o serviço atualizado;
-   implementar as APIs oficiais;
-   tratar erros;
-   manter Webhooks;
-   registrar auditoria;
-   disponibilizar reconexão;
-   acompanhar mudanças da Meta;
-   manter documentação.

------------------------------------------------------------------------

# 53. POLÍTICAS

Antes da produção, estudar:

-   WhatsApp Business Terms;
-   WhatsApp Business Messaging Policy;
-   Meta Platform Terms;
-   políticas de dados;
-   requisitos de templates;
-   regras de mensagens iniciadas pela empresa;
-   regras de qualidade;
-   limites;
-   cobrança;
-   requisitos de App Review.

Fonte principal: https://business.whatsapp.com/policy/preview?lang=pt_BR

------------------------------------------------------------------------

# 54. APP REVIEW

O Embedded Signup oficial informa que o app precisa passar por App
Review para ser lançado e solicitar Advanced Access para permissões
necessárias.

Planejar:

``` text
Desenvolvimento
      ↓
Teste
      ↓
App Review
      ↓
Advanced Access
      ↓
Produção
```

Não esperar até o final para iniciar o processo de revisão.

Fonte:
https://www.postman.com/meta/whatsapp-business-platform/documentation/du6gzjv/embedded-signup

------------------------------------------------------------------------

# 55. AMBIENTE DE DESENVOLVIMENTO

Criar:

``` text
DEV
HOMOLOGAÇÃO
PRODUÇÃO
```

Não misturar:

-   tokens;
-   bancos;
-   Webhooks;
-   números;
-   URLs;
-   credenciais.

------------------------------------------------------------------------

# 56. VARIÁVEIS DE AMBIENTE

Exemplo:

``` text
APP_ENV=development

META_APP_ID=
META_APP_SECRET=
META_GRAPH_VERSION=

META_WEBHOOK_VERIFY_TOKEN=

DATABASE_URL=

LOG_LEVEL=INFO
```

Produção deve utilizar secrets seguros.

------------------------------------------------------------------------

# 57. TESTES AUTOMATIZADOS

Criar testes para:

-   validação de telefone;
-   validação de PDF;
-   autenticação;
-   tratamento de erro;
-   parsing de respostas Meta;
-   Webhook;
-   idempotência;
-   isolamento de empresa;
-   templates;
-   fila;
-   retry;
-   expiração de credencial.

Nunca fazer testes automatizados enviando mensagens reais sem um
ambiente/número de teste apropriado.

------------------------------------------------------------------------

# 58. CRITÉRIOS DE ACEITAÇÃO

O projeto somente será considerado pronto quando:

-   [ ] App Meta configurado.
-   [ ] App Review resolvido.
-   [ ] Embedded Signup funcionando.
-   [ ] Um escritório consegue conectar o próprio WhatsApp.
-   [ ] PH identifica WABA correto.
-   [ ] PH identifica Phone Number ID correto.
-   [ ] Credenciais ficam protegidas.
-   [ ] Texto é enviado.
-   [ ] PDF é enviado.
-   [ ] Template é enviado quando necessário.
-   [ ] Webhook recebe eventos.
-   [ ] Status é gravado.
-   [ ] Erros são tratados.
-   [ ] Dois escritórios podem operar independentemente.
-   [ ] C++ Builder 5 chama Python.
-   [ ] C++ recebe resultado.
-   [ ] Não há segredo Meta no executável.
-   [ ] Logs não expõem tokens.
-   [ ] Documentação do usuário está pronta.
-   [ ] Documentação do desenvolvedor está pronta.
-   [ ] Backup/recovery foi testado.
-   [ ] Segurança foi revisada.

------------------------------------------------------------------------

# 59. ORDEM REAL DE DESENVOLVIMENTO

## Fase 1 --- Pesquisa/validação Meta

1.  Confirmar enquadramento da PH.
2.  Confirmar Embedded Signup.
3.  Confirmar requisitos de App Review.
4.  Confirmar billing.
5.  Confirmar requisitos de número.
6.  Confirmar permissões.
7.  Confirmar Graph API vigente.

## Fase 2 --- Protótipo Meta

8.  Criar app.
9.  Configurar teste.
10. Obter token.
11. Obter WABA.
12. Obter Phone Number ID.
13. Enviar texto.
14. Enviar PDF.

## Fase 3 --- Python

15. Criar projeto.
16. Cliente Graph API.
17. Banco.
18. Envio texto.
19. Media/PDF.
20. Templates.
21. Webhook.
22. Logs.
23. Segurança.

## Fase 4 --- Embedded Signup

24. Criar tela web.
25. Integrar Facebook Login.
26. Integrar Embedded Signup.
27. Callback.
28. Identificar WABA.
29. Registrar/configurar número.
30. Associar recursos conforme fluxo Meta.
31. Validar conexão.

## Fase 5 --- C++

32. Tela WhatsApp.
33. Botão conectar.
34. Abrir onboarding.
35. Status.
36. Envio texto.
37. Envio PDF.
38. Histórico.

## Fase 6 --- Produção

39. HTTPS.
40. Deploy.
41. Monitoramento.
42. App Review.
43. Teste piloto.
44. Documentação.
45. Liberação gradual.

------------------------------------------------------------------------

# 60. INSTRUÇÕES ESPECIAIS PARA A CURSOR

A Cursor deve agir como engenheiro de software sênior e:

1.  Não inventar endpoints.
2.  Não inventar parâmetros.
3.  Não usar documentação antiga sem verificar a data.
4.  Priorizar documentação oficial Meta.
5.  Registrar a URL da documentação usada para cada decisão relevante.
6.  Verificar a versão vigente da Graph API.
7.  Não assumir que o billing é direto do escritório para a Meta.
8.  Não armazenar segredo no C++.
9.  Não criar integração via WhatsApp Web.
10. Não usar bibliotecas não oficiais.
11. Não modificar o legado sem necessidade.
12. Fazer alterações pequenas e compiláveis.
13. Criar testes.
14. Criar logs seguros.
15. Implementar isolamento multiempresa.
16. Confirmar cada requisito da Meta antes de colocá-lo em produção.
17. Quando houver conflito entre documentação antiga e atual, parar e
    apresentar a divergência.
18. Quando houver uma decisão de negócio que não possa ser deduzida
    tecnicamente, não escolher sozinho.
19. Manter uma lista `OPEN_QUESTIONS.md`.
20. Atualizar a documentação do projeto junto com o código.

------------------------------------------------------------------------

# 61. OPEN QUESTIONS --- NÃO CODIFICAR SEM RESOLVER

Estas perguntas devem ser confirmadas pela PH/Meta:

### Q1 --- Billing

A PH quer que:

``` text
Escritório → paga diretamente à Meta
```

ou aceita o modelo:

``` text
Escritório → paga PH
PH → recebe fatura agregada Meta
```

A documentação atual do Embedded Signup descreve explicitamente o
segundo modelo quando a linha de crédito do parceiro é compartilhada.

### Q2 --- Enquadramento da PH

Confirmar se a PH será:

-   Tech Provider;
-   Tech Partner;
-   Solution Partner;

ou outro enquadramento disponível atualmente.

### Q3 --- Número

Confirmar se o número atual de cada escritório será:

-   novo número;
-   número do WhatsApp Business;
-   número em uso;
-   número que precisa de migração;
-   número em coexistência, se suportado para o caso.

### Q4 --- Hospedagem

Definir onde ficará o serviço Python:

-   servidor próprio;
-   VPS;
-   cloud;
-   infraestrutura atual da PH.

### Q5 --- Banco

Definir se o serviço Python acessará:

-   banco existente da PH;
-   banco próprio;
-   API do sistema PH.

### Q6 --- Comunicação C++ ↔ Python

Definir:

-   HTTP interno;
-   HTTPS;
-   VPN;
-   autenticação;
-   porta;
-   firewall.

------------------------------------------------------------------------

# 62. LINKS OFICIAIS PRINCIPAIS

1.  Meta WhatsApp Business Platform: https://business.whatsapp.com/

2.  Developer Hub:
    https://business.whatsapp.com/developers/developer-hub

3.  Coleções oficiais Meta/Postman:
    https://www.postman.com/meta/whatsapp-business-platform/overview

4.  Cloud API:
    https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api

5.  Messages:
    https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ba8d099d-007e-4b52-b9f2-3cf3c60e4fbc

6.  Media:
    https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ecb27be5-4d27-4763-bbee-6a8002c04bf3

7.  Embedded Signup:
    https://www.postman.com/meta/whatsapp-business-platform/documentation/du6gzjv/embedded-signup

8.  Embedded Signup --- Get Started:
    https://www.postman.com/meta/whatsapp-business-platform/collection/du6gzjv/embedded-signup

9.  Embedded Signup --- Credit Line:
    https://www.postman.com/meta/whatsapp-business-platform/folder/kau55oi/step-3-share-line-of-credit-with-a-clients-waba

10. Business Policy:
    https://business.whatsapp.com/policy/preview?lang=pt_BR

11. Pricing: https://business.whatsapp.com/products/platform-pricing/

------------------------------------------------------------------------

# 63. REFERÊNCIAS TÉCNICAS CONFIRMADAS NA PESQUISA DE 21/09/2026

A pesquisa atual confirmou na documentação oficial da Meta:

-   Cloud API é a API oficial hospedada pela Meta.
-   Business Management API é usada para administrar WABAs/ativos.
-   Embedded Signup é o fluxo oficial de onboarding para Solution
    Partners, Tech Providers e Tech Partners.
-   Cloud API usa o endpoint `/PHONE_NUMBER_ID/messages` para mensagens.
-   A API de mensagens suporta texto, mídia e templates.
-   A API de mídia possui endpoints para upload/consulta/exclusão.
-   Webhooks podem ser utilizados para acompanhar eventos/status.
-   WABA pode ser consultada por API.
-   Phone Number ID pode ser obtido por API.
-   A WABA pode ser inscrita no aplicativo para receber Webhooks.
-   Embedded Signup exige App Review/Advanced Access para determinadas
    permissões.
-   O fluxo Embedded Signup exige infraestrutura HTTPS.
-   A documentação atual do Embedded Signup possui fluxo de linha de
    crédito e faturamento agregado, portanto a hipótese de "cada
    escritório recebe diretamente sua fatura da Meta" precisa ser
    validada antes da implementação final.

Fontes: https://www.postman.com/meta/whatsapp-business-platform/overview
https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api
https://www.postman.com/meta/whatsapp-business-platform/documentation/du6gzjv/embedded-signup
https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ba8d099d-007e-4b52-b9f2-3cf3c60e4fbc
https://www.postman.com/meta/whatsapp-business-platform/folder/13382743-ecb27be5-4d27-4763-bbee-6a8002c04bf3
https://business.whatsapp.com/policy/preview?lang=pt_BR

------------------------------------------------------------------------

# 64. COMANDO INICIAL PARA A CURSOR

Antes de modificar qualquer código, a Cursor deve ler este documento
inteiro e executar uma fase de análise.

Prompt recomendado:

> Você é um engenheiro de software sênior especializado em C++ Builder
> legado, Python, APIs REST, segurança e integração com Meta WhatsApp
> Business Platform.
>
> Leia integralmente este documento.
>
> Não comece alterando o código.
>
> Primeiro analise o projeto PH existente e produza:
>
> 1.  arquitetura atual;
> 2.  bibliotecas HTTP existentes;
> 3.  bibliotecas JSON existentes;
> 4.  acesso ao banco;
> 5.  padrão de telas/forms;
> 6.  pontos adequados para integração;
> 7.  infraestrutura atual;
> 8.  versão Python disponível;
> 9.  riscos de compatibilidade com C++ Builder 5;
> 10. requisitos Meta que ainda precisam ser confirmados.
>
> Depois compare a arquitetura existente com este manual.
>
> Consulte somente documentação oficial atual da Meta para decisões
> sobre WhatsApp.
>
> Não invente endpoints, parâmetros, permissões, limites, preços ou
> comportamentos.
>
> Gere primeiro um plano técnico e uma lista de perguntas/decisões
> pendentes.
>
> Aguarde aprovação antes de realizar alterações estruturais no sistema.

------------------------------------------------------------------------

# 65. REGRA FINAL

Este documento é um **roteiro técnico inicial baseado na documentação
encontrada em 21/09/2026**.

A implementação deve tratar a documentação oficial da Meta como fonte
viva.

Sempre que a Meta alterar:

-   Graph API;
-   Embedded Signup;
-   permissões;
-   billing;
-   templates;
-   Webhooks;
-   limites;
-   requisitos de número;
-   App Review;

o sistema deverá ser reavaliado.

**Nunca transformar uma informação encontrada em blog, fórum, vídeo ou
resposta de IA em requisito técnico sem confirmar na documentação
oficial da Meta.**
