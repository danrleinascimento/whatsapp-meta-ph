WHATSPH — Instalacao (PH Softwares)
===================================

Pre-requisitos
--------------
- Windows 10/11 (ou Server) 64-bit
- Postgres com banco whatsapp_ph (ou ajustar DATABASE_URL no .env)
- Porta 127.0.0.1:8765 livre
- GEPH/PH apontando para a mesma pasta PHSFTW

Apos o Setup
------------
1. Editar C:\PHSFTW\WHATSPH\.env e descomentar/ajustar DATABASE_URL
2. Rodar apply_sql.bat (se o Setup falhou no SQL)
3. services.msc → PHWhatsMeta = Em execucao
4. Abrir http://127.0.0.1:8765/health  → role=agent, db_ok=true
5. Nao abrir o painel sem ticket do GEPH (retorna bloqueado)

Logs
----
C:\PHSFTW\WHATSPH\logs\service_stdout.log
C:\PHSFTW\WHATSPH\logs\service_stderr.log

Seguranca
---------
- Nunca coloque META_APP_SECRET no .env do escritorio
- HUB_PULL_SECRET deve ser igual ao do hub DigitalOcean
- Painel so via menu GEPH (ticket HMAC)

Suporte PH Softwares
--------------------
Hub: https://whatsapp-meta-ph-wzewk.ondigitalocean.app
