@echo off
set APPDIR=%~dp0
cd /d "%APPDIR%"
if not exist "%APPDIR%.venv\Scripts\python.exe" (
  echo ERRO: .venv nao encontrado. Rode build_dist antes de instalar.
  exit /b 1
)
"%APPDIR%.venv\Scripts\python.exe" "%APPDIR%first_run.py" --app-dir "%APPDIR%" --phsftw-root "%APPDIR%.."
if errorlevel 1 exit /b 1
echo first_run OK
