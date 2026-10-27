# Roteiro: aprovação do app Meta e liberação do "Conectar conta WhatsApp"

Atualizado em 27/10/2026. Detalhes técnicos: seção 15 do `documentacao.md`.

**Decisão do usuário:** os escritórios usam o mesmo número que já usam no app WhatsApp Business (coexistência, com sincronização do histórico).

## Onde acompanhar

- Painel do app: https://developers.facebook.com/apps/2053406131958490/dashboard/
- Status da análise: https://developers.facebook.com/apps/2053406131958490/app-review/submissions/ (no painel, menu **Analisar > Análise do app**).
- Alertas: menu **Caixa de Entrada de alertas**, no painel do app. Os e-mails de `noreply@developers.facebook.com` chegam em `danrlei@phnet.com.br`.
- App: PH Softwares, ID `2053406131958490`. Empresa: PH Softwares, ID `2298670120886101`.

## Situação em 27/10/2026

- Análise enviada em 27/10/2026, às 08:58. Status "Análise em andamento", prazo de até 20 dias.
- Permissões pedidas: `whatsapp_business_messaging`, `whatsapp_business_management`, `public_profile`.
- URL de teste enviada à Meta: `https://whatsapp-meta-ph-wzewk.ondigitalocean.app/onboarding?installation_id=meta-review`, com dois vídeos.
- Itens do painel:
  - Verdes: caso de uso do WhatsApp, requisitos de teste, verificação da empresa e análise do app (enviada).
  - Sem o verde: "Login do Facebook para Empresas", que é a configuração criada depois da aprovação, e "Verifique todos os requisitos", que fica verde com a aprovação.
  - App ainda "Não publicado".

## Já foi feito

### Meta

- App com o caso de uso "Conectar-se com os clientes pelo WhatsApp".
- Empresa verificada.
- Política de privacidade publicada em `https://phsoftwares.com.br/privacidade.php`.
- Modelos `ph_boleto_pdf` e `ph_relatorio_pdf` aprovados na conta da PH.

### Hub (DigitalOcean, publicado na versão 0.4.1)

- Deploy pelo GitHub `danrleinascimento/whatsapp-meta-ph`, branch `main`. Commits `9435428` (0.4.0) e `540648c` (0.4.1).
- A página `/onboarding` abre o cadastro no modo de conta existente do WhatsApp Business (`featureType: whatsapp_business_app_onboarding`).
- Depois do cadastro, o hub:
  1. troca o código da Meta pelo acesso;
  2. descobre a conta WhatsApp pelo evento ou pelo `debug_token`;
  3. chama `subscribed_apps`;
  4. confere `is_on_biz_app` e `platform_type`;
  5. pede a sincronização de contatos e depois a de histórico (`smb_app_data`, uma vez cada; só repete se o pedido não saiu).
- O histórico e os contatos sincronizados não são gravados, só o progresso no log.
- Correções de segurança:
  - o App Secret não vai mais para o log;
  - os parâmetros da página são validados e escapados.

### Serviço WHATSPH (código pronto na 0.4.1; falta gerar o exe e o instalador)

- O GEPH chama `POST /v1/whatsapp/onboarding/start`. O serviço gera um código de cadastro que vale 1 h e devolve o link da página.
- O serviço busca o resultado no hub a cada 10 s e grava a conta como `CONNECTED`, com o token cifrado.
- Não perde o cadastro em caso de dois cliques em "Conectar" ou de reinício do serviço. Vale qualquer código da última hora (até 10), e os códigos ficam em `onboarding_pendente.json`, sem o token.
- Cria na conta do escritório os modelos `ph_boleto_pdf` e `ph_relatorio_pdf` que faltarem. Usa o mesmo texto dos modelos da PH, e a Meta precisa aprovar os modelos de cada escritório.

### GEPH (fontes em `C:\CBuilder5\Projects\Lib\phvcl`; sem compilar e sem commit SVN)

- `WhatsMetaClient.h` e `WhatsMetaClient.cpp`: nova função `StartOnboarding`. Com o serviço antigo (HTTP 404), avisa para atualizar o WHATSPH.
- `WhatsMetaUi.cpp`: "Conectar conta WhatsApp":
  1. confere se o serviço está no ar;
  2. se a conta já estiver conectada, pede confirmação;
  3. pede o link ao serviço e abre o navegador.
- Os três arquivos continuam em CP1252, sem BOM e com CRLF; a codificação foi conferida contra o SVN BASE.

### Testes

- Teste local com a Meta e o hub simulados: tudo passou. Cobre coexistência, erros, número fora do app, dois cliques, reinício, sincronização sem repetição duvidosa e criação de modelos.
- Ainda não testados com a Meta real: o cadastro completo e a criação de modelos na conta do escritório. Só depois da aprovação.

## Enquanto aguarda a aprovação

- Não alterar as configurações do app na Meta.
- Não mexer na política de privacidade.
- Não apagar o modelo `ph_teste_revisao`.
- Manter o hub no ar.
- Se a Meta pedir algo (por exemplo, a verificação de acesso ou uma correção), responder pelo painel.

## Já pode fazer (não depende da Meta)

1. Gerar o `whatsph.exe` e o instalador 0.4.1:
   ```powershell
   cd C:\projetos\python\whatsmeta
   .\scripts\build_exe.ps1
   .\scripts\build_instalador.ps1
   ```
   Saída: `instalador\saida\instalarWHATSPH.exe`.
2. Instalar o WHATSPH 0.4.1 nesta máquina e conferir se `/health` responde 0.4.1.
3. Rebuild do `PH.bpl` e do GEPH no C++ Builder 5.
4. Fazer o commit SVN dos três fontes do `Lib\phvcl` (quando o usuário quiser).

## Depois da aprovação (nesta ordem)

1. **Webhook:** em WhatsApp > Configuração, assinar os campos `history`, `smb_app_state_sync`, `smb_message_echoes` e `account_update`. O `messages` já está assinado.
2. **Publicar o app** pelo menu "Publicar".
3. **Configuração do cadastro:** em "Login do Facebook para Empresas" > Configurações, criar uma configuração do tipo WhatsApp Embedded Signup com validade do token **"Nunca"**. Copiar o ID.
4. **DigitalOcean:** colocar o ID em `META_EMBEDDED_SIGNUP_CONFIG_ID` nas variáveis do app. O hub reinicia sozinho. Até aqui o botão "Conectar" não funciona para os escritórios.
5. **Escritório piloto:**
   1. GEPH > Conectar conta WhatsApp, com o celular do WhatsApp Business aberto;
   2. concluir na página;
   3. em até 1 minuto, a Situação do WhatsApp deve mostrar a conta conectada;
   4. enviar um boleto de teste;
   5. conferir no log do serviço (`logs\whatsph.log`) a criação dos modelos.
6. **Pagamento:** o escritório cadastra a forma de pagamento em https://business.facebook.com/wa/manage/home/. Sem isso, não envia para quem não conversou com ele nas últimas 24 h.
7. **Distribuição:** levar o WHATSPH 0.4.1 e o GEPH novo para os demais escritórios.

## Cuidados no cadastro de cada escritório

- O celular com o WhatsApp Business precisa ficar aberto durante o cadastro e alguns minutos depois (sincronização).
- A Meta só aceita os pedidos de sincronização até 24 h depois do cadastro, uma vez cada. Se falhar, o escritório precisa desconectar no app (Configurações > Conta > Business Platform > Desconectar) e refazer o cadastro.
- Na coexistência o número fica limitado a 20 mensagens por segundo, um limite da Meta.
- Se a página mostrar "Atenção" (por exemplo, falha na sincronização ou acesso com validade), anotar e verificar o log do hub na DigitalOcean.

## Para o agente retomar

Ler este arquivo e a seção 15 do `documentacao.md`. Regras do projeto:

- Os fontes `.cpp`, `.h` e `.dfm` são CP1252 e só podem ser alterados por script Python binário.
- Nada de commit ou push sem pedido do usuário.
- Não repetir segredos do `.env`.
- O usuário decidiu não trocar o App Secret.
