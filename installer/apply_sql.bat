@echo off
REM Aplica sql/001..003 usando DATABASE_URL do .env
set APPDIR=%~dp0
cd /d "%APPDIR%"
if not exist "%APPDIR%.venv\Scripts\python.exe" (
  echo ERRO: .venv nao encontrado
  exit /b 1
)
if not exist "%APPDIR%.env" (
  echo ERRO: .env ausente — rode first_run.bat antes
  exit /b 1
)
"%APPDIR%.venv\Scripts\python.exe" "%APPDIR%scripts\apply_sql.py"
if errorlevel 1 (
  echo ERRO apply_sql — confira DATABASE_URL no .env
  exit /b 1
)
echo apply_sql OK
