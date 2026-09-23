@echo off
REM Instala servico Windows PHWhatsMeta via NSSM
set APPDIR=%~dp0
set NSSM=%APPDIR%nssm\nssm.exe
set LOGDIR=%APPDIR%logs
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
if not exist "%NSSM%" (
  echo ERRO: nssm.exe nao encontrado em %APPDIR%nssm\
  echo Baixe NSSM win64 e coloque nssm.exe em WHATSPH\nssm\
  exit /b 1
)
if not exist "%APPDIR%.venv\Scripts\python.exe" (
  echo ERRO: .venv\Scripts\python.exe ausente
  exit /b 1
)
"%NSSM%" stop PHWhatsMeta >nul 2>&1
"%NSSM%" remove PHWhatsMeta confirm >nul 2>&1
"%NSSM%" install PHWhatsMeta "%APPDIR%.venv\Scripts\python.exe" "-m" "uvicorn" "app.main:app" "--host" "127.0.0.1" "--port" "8765"
"%NSSM%" set PHWhatsMeta AppDirectory "%APPDIR%"
"%NSSM%" set PHWhatsMeta AppEnvironmentExtra APP_ROLE=agent
"%NSSM%" set PHWhatsMeta AppStdout "%LOGDIR%\service_stdout.log"
"%NSSM%" set PHWhatsMeta AppStderr "%LOGDIR%\service_stderr.log"
"%NSSM%" set PHWhatsMeta AppRotateFiles 1
"%NSSM%" set PHWhatsMeta AppRotateBytes 2097152
"%NSSM%" set PHWhatsMeta Start SERVICE_AUTO_START
"%NSSM%" start PHWhatsMeta
echo Servico PHWhatsMeta instalado e iniciado.
echo Logs: %LOGDIR%
