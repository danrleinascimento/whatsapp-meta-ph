[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExecutavelOrigem,
    [string]$Diretorio = "",
    [int]$TempoEspera = 60,
    [string]$ArquivoResultado = ""
)

# Instala ou atualiza o servico Windows PHWhatsMeta a partir do whatsph.exe
# (mesmo modelo do preparar_ambiente_huph.ps1). Destino padrao: <PHSFTW>\SERVICOS\WHATSPH.
# Sem .env no destino, copia <PHSFTW>\WHATSPH\.env (pasta da instalacao antiga) se existir:
# PH_API_KEY, INSTALLATION_ID e TOKEN_ENCRYPTION_KEY precisam continuar os mesmos.
# PHWhatsMeta registrado com outro executavel: o script recusa sem alterar nada.
# Banco: 'whatsph.exe preparar-banco' cria o banco do DATABASE_URL se faltar e cria/atualiza as tabelas.
# ArquivoResultado: grava tambem o JSON final nesse arquivo (usado pelo instalarWHATSPH.exe).

$ErrorActionPreference = "Stop"
$NomeServico = "PHWhatsMeta"
$etapa = "validacao"
$bloqueado = $false
$mutex = $null
$local_alterado = $false

function executarWhatsph([string[]]$Argumentos) {
    $saida = & $destino @Argumentos 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Comando whatsph falhou: $($Argumentos[0]) - $($saida -join ' ')"
    }
    return ($saida -join "`n")
}

function emitirResultado([hashtable]$Dados) {
    $json = $Dados | ConvertTo-Json -Depth 5 -Compress
    if (-not [string]::IsNullOrWhiteSpace($ArquivoResultado)) {
        try { [IO.File]::WriteAllText($ArquivoResultado, $json, [Text.Encoding]::Default) } catch { }
    }
    return $json
}

function copiarExecutavel([string]$origem, [string]$destino, [int]$tempo_espera) {
    $relogio = [Diagnostics.Stopwatch]::StartNew()
    while ($true) {
        try {
            [IO.File]::Copy($origem, $destino, $true)
            return
        } catch {
            $erro = $_.Exception
            while ($null -ne $erro.InnerException) { $erro = $erro.InnerException }
            $codigo = $erro.HResult -band 0xFFFF
            if ($codigo -notin @(32, 33)) { throw }
            if ($relogio.Elapsed.TotalSeconds -ge $tempo_espera) {
                throw "Executavel ainda em uso apos $tempo_espera segundos: $destino. Verifique processos whatsph remanescentes ou iniciados manualmente."
            }
            Start-Sleep -Milliseconds 250
        }
    }
}

function obterExecutavelRegistrado([string]$PathName) {
    $texto = $PathName.Trim()
    if ($texto.StartsWith('"')) {
        return $texto.Substring(1, $texto.IndexOf('"', 1) - 1)
    }
    $fim = $texto.IndexOf(' ')
    if ($fim -lt 0) { return $texto }
    return $texto.Substring(0, $fim)
}

try {
    $identidade = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identidade)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Execute com privilegios administrativos"
    }
    if ($TempoEspera -lt 1 -or $TempoEspera -gt 600) {
        throw "TempoEspera deve estar entre 1 e 600 segundos"
    }
    $mutex = New-Object Threading.Mutex($false, "Global\WHATSPH_Preparacao")
    try {
        $bloqueado = $mutex.WaitOne(0)
    } catch [Threading.AbandonedMutexException] {
        $bloqueado = $true
    }
    if (-not $bloqueado) {
        throw "Outra preparacao WHATSPH esta em andamento"
    }
    $origem = (Resolve-Path -LiteralPath $ExecutavelOrigem).Path
    if (-not (Test-Path -LiteralPath $origem -PathType Leaf)) {
        throw "Executavel de origem nao encontrado"
    }
    if ([string]::IsNullOrWhiteSpace($Diretorio)) {
        $raiz_ph = [IO.DirectoryInfo](Split-Path -Parent $origem)
        while ($null -ne $raiz_ph -and $raiz_ph.Name -ine 'PHSFTW') {
            $raiz_ph = $raiz_ph.Parent
        }
        if ($null -eq $raiz_ph) {
            throw "Raiz PHSFTW nao encontrada na origem; informe Diretorio"
        }
        $Diretorio = Join-Path $raiz_ph.FullName 'SERVICOS\WHATSPH'
    }
    $pasta = [IO.Path]::GetFullPath($Diretorio).TrimEnd('\')
    $raiz_ph = [IO.DirectoryInfo]$pasta
    while ($null -ne $raiz_ph -and $raiz_ph.Name -ine 'PHSFTW') {
        $raiz_ph = $raiz_ph.Parent
    }
    $raiz_servicos = $null
    if ($null -ne $raiz_ph) { $raiz_servicos = Join-Path $raiz_ph.FullName 'SERVICOS' }
    if ($null -eq $raiz_servicos -or -not $pasta.StartsWith($raiz_servicos + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Diretorio deve ficar na estrutura PHSFTW\SERVICOS"
    }
    $destino = Join-Path $pasta "whatsph.exe"
    $arquivo_env = Join-Path $pasta ".env"

    $servico = Get-Service -Name $NomeServico -ErrorAction SilentlyContinue
    $primeira_instalacao = $null -eq $servico
    if ($null -ne $servico) {
        $registro = Get-CimInstance Win32_Service -Filter "Name='$NomeServico'"
        $exe_registrado = obterExecutavelRegistrado $registro.PathName
        if ($exe_registrado -ine $destino) {
            throw "$NomeServico registrado com outro executavel ($exe_registrado); use o diretorio da instalacao existente ou remova o servico antigo (sc delete $NomeServico)"
        }
    }

    $etapa = "parada"
    if ($null -ne $servico -and $servico.Status -ne 'Stopped') {
        Stop-Service -Name $NomeServico -Force
        $servico.WaitForStatus('Stopped', [TimeSpan]::FromSeconds($TempoEspera))
    }

    $etapa = "arquivos"
    New-Item -ItemType Directory -Path $pasta -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $pasta 'logs') -Force | Out-Null
    if ($origem -ine $destino) {
        copiarExecutavel -origem $origem -destino $destino -tempo_espera $TempoEspera
    }
    Push-Location -LiteralPath $pasta
    $local_alterado = $true
    $versao = (executarWhatsph -Argumentos @('version')).Trim()

    $etapa = "configuracao"
    $configuracao = "existente"
    if (-not (Test-Path -LiteralPath $arquivo_env -PathType Leaf)) {
        # Chaves novas quebrariam o GEPH (PH_API_KEY) e o token da Meta no banco (TOKEN_ENCRYPTION_KEY).
        $env_legado = Join-Path $raiz_ph.FullName "WHATSPH\.env"
        if (Test-Path -LiteralPath $env_legado -PathType Leaf) {
            Copy-Item -LiteralPath $env_legado -Destination $arquivo_env
            $configuracao = "copiada de $env_legado"
        } else {
            executarWhatsph -Argumentos @('gerar-configuracao') | Out-Null
            $configuracao = "gerada"
        }
    }

    $etapa = "banco"
    $saida_banco = & $destino 'preparar-banco' 2>&1
    $codigo_banco = $LASTEXITCODE
    $banco = $null
    try { $banco = ($saida_banco -join "`n") | ConvertFrom-Json } catch { $banco = $null }
    if ($codigo_banco -ne 0 -or $null -eq $banco -or $banco.status -ne 'SUCESSO') {
        $motivo_banco = $saida_banco -join ' '
        if ($null -ne $banco -and $banco.mensagem) { $motivo_banco = $banco.mensagem }
        throw "Banco nao preparado (DATABASE_URL de $arquivo_env): $motivo_banco"
    }

    $etapa = "registro_servico"
    if ($null -ne $servico) {
        executarWhatsph -Argumentos @('update-service') | Out-Null
    } else {
        executarWhatsph -Argumentos @('install-service') | Out-Null
    }

    $etapa = "inicializacao"
    Start-Service -Name $NomeServico
    $servico = Get-Service -Name $NomeServico
    $servico.WaitForStatus('Running', [TimeSpan]::FromSeconds($TempoEspera))

    $etapa = "saude"
    $limite = (Get-Date).AddSeconds($TempoEspera)
    $pronto = $false
    do {
        try {
            $saude = executarWhatsph -Argumentos @('verificar-servico', '--timeout', '2') | ConvertFrom-Json
            $servico.Refresh()
            $pronto = $saude.status -eq 'ok' -and $saude.role -eq 'agent' -and $saude.version -eq $versao
            $pronto = $pronto -and $servico.Status -eq 'Running'
        } catch {
            $pronto = $false
        }
        if ($pronto) { break }
        Start-Sleep -Seconds 1
    } while ((Get-Date) -lt $limite)
    if (-not $pronto) {
        throw "Servico sem resposta de saude na versao instalada; consulte logs\whatsph.log e logs\whatsph-service.log"
    }

    $acao = 'atualizado'
    if ($primeira_instalacao) { $acao = 'instalado' }
    emitirResultado -Dados @{
        codigo = 'WHATSPH_AMBIENTE_PRONTO'; status = 'SUCESSO'; versao = $versao
        mensagem = "WHATSPH $versao $acao em $pasta. Servico em execucao e respondendo."
        diretorio = $pasta; primeira_instalacao = $primeira_instalacao
        configuracao = $configuracao; db_ok = $saude.db_ok; banco_criado = [bool]$banco.banco_criado
    }
    exit 0
} catch {
    $mensagem_erro = $_.Exception.Message
    # Falha depois da parada: tenta religar o servico que ficou registrado (versao antiga ou nova).
    $servico_religado = $false
    if ($etapa -notin @('validacao', 'parada')) {
        try {
            $restante = Get-Service -Name $NomeServico -ErrorAction SilentlyContinue
            if ($null -ne $restante -and $restante.Status -eq 'Stopped') {
                Start-Service -Name $NomeServico -ErrorAction Stop
                $servico_religado = $true
            }
        } catch {
            $servico_religado = $false
        }
    }
    emitirResultado -Dados @{
        codigo = 'WHATSPH_PREPARACAO_FALHA'; status = 'ERRO'; etapa = $etapa
        mensagem = "Falha na etapa '$etapa': $mensagem_erro"; servico_religado = $servico_religado
    }
    exit 1
} finally {
    if ($local_alterado) { Pop-Location }
    if ($bloqueado) { $mutex.ReleaseMutex() }
    if ($null -ne $mutex) { $mutex.Dispose() }
}
