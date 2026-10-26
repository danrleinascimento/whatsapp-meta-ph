# Gera dist\whatsph.exe (agente WHATSPH + servico Windows PHWhatsMeta), no modelo do huph.exe.
# Uso:
#   cd C:\projetos\python\whatsmeta
#   .\scripts\build_exe.ps1
# Publicar: dist\whatsph.exe + scripts\preparar_ambiente_whatsph.ps1

# pip e PyInstaller escrevem progresso no stderr: falha e decidida pelo $LASTEXITCODE.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Py)) {
    throw "Ambiente .venv ausente. Crie com: python -m venv .venv"
}
& $Py -m pip install --disable-pip-version-check -q -r (Join-Path $Root "requirements-dev.txt")
if ($LASTEXITCODE -ne 0) { throw "pip install falhou" }

if (-not (Test-Path -LiteralPath (Join-Path $Root "web\dist\index.html"))) {
    Push-Location (Join-Path $Root "web")
    if (-not (Test-Path "node_modules")) { npm ci }
    npm run build
    Pop-Location
}

& $Py -m PyInstaller --noconfirm --clean whatsph.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou" }

$Exe = Join-Path $Root "dist\whatsph.exe"
$Versao = "$(& $Exe version)".Trim()
if ($LASTEXITCODE -ne 0) { throw "dist\whatsph.exe nao executou" }
$Sha1 = (Get-FileHash -Algorithm SHA1 -LiteralPath $Exe).Hash
Write-Output "OK $Exe versao $Versao SHA1 $Sha1"
