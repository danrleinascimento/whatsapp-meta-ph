# Gera instalador\saida\instalarWHATSPH.exe (Inno Setup) com dist\whatsph.exe + preparar_ambiente_whatsph.ps1.
# Uso:
#   cd C:\projetos\python\whatsmeta
#   .\scripts\build_exe.ps1
#   .\scripts\build_instalador.ps1
# O mesmo instalarWHATSPH.exe instala (1a vez) e atualiza o servico PHWhatsMeta no cliente.

# ISCC escreve progresso no stderr: falha e decidida pelo $LASTEXITCODE.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot

$Exe = Join-Path $Root "dist\whatsph.exe"
if (-not (Test-Path -LiteralPath $Exe)) {
    throw "dist\whatsph.exe ausente. Rode antes .\scripts\build_exe.ps1"
}
$Versao = "$(& $Exe version)".Trim()
if ($LASTEXITCODE -ne 0 -or $Versao -notmatch '^\d+\.\d+\.\d+$') {
    throw "Versao invalida do dist\whatsph.exe: '$Versao'"
}

# whatsph.iss e testado no Inno Setup 5.5.9 ANSI (mesmo do instalador do RTPH).
$Iscc = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 5\ISCC.exe"
if (-not (Test-Path -LiteralPath $Iscc)) { throw "Inno Setup 5 nao encontrado: $Iscc" }

& $Iscc /Q "/DMyAppVersion=$Versao" (Join-Path $Root "instalador\whatsph.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC falhou (codigo $LASTEXITCODE)" }

$Instalador = Join-Path $Root "instalador\saida\instalarWHATSPH.exe"
$Sha1 = (Get-FileHash -Algorithm SHA1 -LiteralPath $Instalador).Hash
Write-Output "OK $Instalador versao $Versao SHA1 $Sha1"
