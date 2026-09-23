# Build pasta dist\whatsph para o Inno Setup.
# Uso (PowerShell Admin opcional):
#   cd C:\projetos\python\whatsmeta
#   .\scripts\build_dist.ps1
# Depois: colocar nssm.exe em dist\whatsph\nssm\ e compilar installer\WHATSPH.iss

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "app\main.py"))) {
  $Root = "C:\projetos\python\whatsmeta"
}
Set-Location $Root
Write-Host "ROOT=$Root"

$Dist = Join-Path $Root "dist\whatsph"
if (Test-Path $Dist) {
  Write-Host "Removendo dist\whatsph antigo..."
  Remove-Item -Recurse -Force $Dist
}
New-Item -ItemType Directory -Path $Dist | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Dist "logs") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Dist "nssm") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $Dist "web") | Out-Null

Write-Host "Build web (React)..."
Push-Location (Join-Path $Root "web")
if (-not (Test-Path "node_modules")) { npm ci }
npm run build
Pop-Location

Write-Host "Copiando app, sql, scripts, web\dist..."
Copy-Item -Recurse (Join-Path $Root "app") (Join-Path $Dist "app")
Copy-Item -Recurse (Join-Path $Root "sql") (Join-Path $Dist "sql")
Copy-Item -Recurse (Join-Path $Root "scripts") (Join-Path $Dist "scripts")
Copy-Item -Recurse (Join-Path $Root "web\dist") (Join-Path $Dist "web\dist")
Copy-Item (Join-Path $Root "requirements.txt") (Join-Path $Dist "requirements.txt")
Copy-Item (Join-Path $Root "installer\first_run.py") (Join-Path $Dist "first_run.py")
Copy-Item (Join-Path $Root "installer\first_run.bat") (Join-Path $Dist "first_run.bat")
Copy-Item (Join-Path $Root "installer\apply_sql.bat") (Join-Path $Dist "apply_sql.bat")
Copy-Item (Join-Path $Root "installer\install_service.bat") (Join-Path $Dist "install_service.bat")
Copy-Item (Join-Path $Root "installer\README_INSTALACAO.txt") (Join-Path $Dist "README_INSTALACAO.txt") -ErrorAction SilentlyContinue

# Limpar caches Python
Get-ChildItem -Path (Join-Path $Dist "app") -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Criando .venv embutido (pode demorar)..."
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
& $Py -m venv (Join-Path $Dist ".venv")
& (Join-Path $Dist ".venv\Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $Dist ".venv\Scripts\python.exe") -m pip install -r (Join-Path $Dist "requirements.txt")

$NssmHint = Join-Path $Dist "nssm\COLOQUE_nssm.exe_AQUI.txt"
@"
Baixe NSSM (https://nssm.cc/download), extraindo nssm.exe (win64)
para esta pasta: dist\whatsph\nssm\nssm.exe
"@ | Set-Content -Path $NssmHint -Encoding ASCII

Write-Host ""
Write-Host "OK dist\whatsph pronto."
Write-Host "1) Copie nssm.exe para dist\whatsph\nssm\"
Write-Host "2) Compile installer\WHATSPH.iss no Inno Setup 6"
Write-Host "3) Teste WHATSPH_Setup_0.2.4.exe em VM"
