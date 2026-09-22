# Integracao PHVCL — WhatsMetaClient (N6)

## Arquivos novos
- `C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.h`
- `C:\CBuilder5\Projects\Lib\phvcl\WhatsMetaClient.cpp`

## Arquivos alterados
- `SenWA.cpp` — tenta Cloud API antes do FTP/Whats.exe
- `Preview.cpp` — include do client (envio continua via form SenWA)

## No projeto PH.bpl (BCB5)
1. Project → Add to Project → `WhatsMetaClient.cpp`
2. Garantir package Indy (`IdHTTP`) linkado (ja usado em Miscelan)
3. Rebuild PH.bpl + GEPH (CP1252)

## Runtime no cliente
- Servico WHATSPH em `127.0.0.1:8765`
- Arquivo `{PHSFTW}\WHATSPH\.env` com `PH_API_KEY`
- Status CONECTADO (seed ou pairing)

## Comportamento
- Telefone obrigatorio 11 digitos no form SenWA para Meta
- Se agente offline / desconectado → fluxo legado Whats.exe intacto
