@echo off
REM Instala servico Windows via NSSM (colocar nssm.exe em WHATSPH\nssm\)
set APPDIR=%~dp0
set NSSM=%APPDIR%nssm\nssm.exe
if not exist "%NSSM%" (
  echo ERRO: nssm.exe nao encontrado em %APPDIR%nssm\
  exit /b 1
)
"%NSSM%" stop PHWhatsMeta >nul 2>&1
"%NSSM%" remove PHWhatsMeta confirm >nul 2>&1
"%NSSM%" install PHWhatsMeta "%APPDIR%.venv\Scripts\python.exe" "-m" "uvicorn" "app.main:app" "--host" "127.0.0.1" "--port" "8765"
"%NSSM%" set PHWhatsMeta AppDirectory "%APPDIR%"
"%NSSM%" set PHWhatsMeta AppEnvironmentExtra APP_ROLE=agent
"%NSSM%" set PHWhatsMeta Start SERVICE_AUTO_START
"%NSSM%" start PHWhatsMeta
echo Servico PHWhatsMeta instalado.
