#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$InfraDbDir = Join-Path $ProjectRoot "infra\docker\databases"

$StateDir = Join-Path $ProjectRoot ".dev_runtime"
$PidDir = Join-Path $StateDir "pids"
$LogDir = Join-Path $StateDir "logs"

New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$ComposeEnvFile = ""
if (Test-Path (Join-Path $ProjectRoot ".env.local")) {
    $ComposeEnvFile = Join-Path $ProjectRoot ".env.local"
} elseif (Test-Path (Join-Path $ProjectRoot ".env")) {
    $ComposeEnvFile = Join-Path $ProjectRoot ".env"
} else {
    Write-Error "[err] No se encontró .env.local ni .env en la raíz del proyecto"
    exit 1
}

$Stacks = @("mssql", "mysql", "mongo", "neo4j", "supabase")

$script:MssqlMode = "remote"
$MssqlRemoteCompose = Join-Path $InfraDbDir "mssql\compose.yaml"
$MssqlLocalCompose = Join-Path $InfraDbDir "mssql\compose.localdb.yaml"
$MssqlInitContainerRemote = "mssql_sales_init"
$MssqlInitContainerLocal = "mssql_sales_init_local"
$SupabaseCompose = Join-Path $InfraDbDir "supabase\compose.yaml"
$SupabaseInitContainer = "supabase_sales_init"

$script:DbComposeFiles = @{
    mssql    = $MssqlRemoteCompose
    mysql    = Join-Path $InfraDbDir "mysql\compose.yaml"
    mongo    = Join-Path $InfraDbDir "mongo\compose.yaml"
    neo4j    = Join-Path $InfraDbDir "neo4j\compose.yaml"
    supabase = $SupabaseCompose
}

$BackendPaths = @{
    mssql    = Join-Path $ProjectRoot "services\api-mssql"
    mysql    = Join-Path $ProjectRoot "services\api-mysql"
    mongo    = Join-Path $ProjectRoot "services\api-mongo"
    neo4j    = Join-Path $ProjectRoot "services\api-neo4j"
    supabase = Join-Path $ProjectRoot "services\api-supabase"
}

$BackendRunners = @{
    mssql    = "bun"
    mysql    = "bun"
    mongo    = "uv"
    neo4j    = "uv"
    supabase = "uv"
}

$BackendPortDefaults = @{
    mssql    = 3000
    mysql    = 3001
    mongo    = 3002
    neo4j    = 3003
    supabase = 3004
}

$FrontendPaths = @{
    mssql    = Join-Path $ProjectRoot "apps\web-mssql"
    mysql    = Join-Path $ProjectRoot "apps\web-mysql"
    mongo    = Join-Path $ProjectRoot "apps\web-mongo"
    neo4j    = Join-Path $ProjectRoot "apps\web-neo4j"
    supabase = Join-Path $ProjectRoot "apps\web-supabase"
}

$FrontendRunners = @{
    mssql    = "bun"
    mysql    = "bun"
    mongo    = "pnpm"
    neo4j    = "pnpm"
    supabase = "pnpm"
}

$FrontendPortDefaults = @{
    mssql    = 5000
    mysql    = 5001
    mongo    = 5002
    neo4j    = 5003
    supabase = 5004
}

$InitMaxWait = @{
    mssql    = 300
    mysql    = 300
    mongo    = 300
    neo4j    = 300
    supabase = 0
}

$script:OpenIndexAfter = $false
$script:MssqlModeExplicit = $false

function Log-Warn {
    param([string]$Message)
    Write-Host "[warn] $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "[err] $Message" -ForegroundColor Red
}

function Log-Info {
    param([string]$Message)
    Write-Host "[info] $Message" -ForegroundColor Cyan
}

function Open-IndexHtml {
    $indexFile = Join-Path $ProjectRoot "index.html"
    if (-not (Test-Path $indexFile)) {
        Log-Warn "No se encontró index.html en $ProjectRoot"
        return
    }
    Start-Process $indexFile
}

function Show-Help {
    @"
Uso: .\scripts\dev.ps1 [-Up|-Down|-Init] [stack1,stack2,...]
    [-Local|-Remote]

Stacks disponibles:
  mssql, mysql, mongo, neo4j, supabase, all

Acciones:
  -Up    Levanta base de datos, backend y frontend en ese orden
  -Down  Detiene frontend, backend y baja la base de datos
  -Init  Re-crea la base de datos con el perfil init y vuelve a levantar todo

Ejemplos:
  .\scripts\dev.ps1 -Up mssql
  .\scripts\dev.ps1 -Down mysql
  .\scripts\dev.ps1 -Init all
  .\scripts\dev.ps1 -Init mssql,mysql
  .\scripts\dev.ps1 -Down mssql,mysql,mongo

Modos MSSQL:
  -Remote (por defecto)  Usa la instancia externa configurada en .env*
  -Local                 Levanta el contenedor local de SQL Server e ignora los jobs BCCR
"@
}

function Set-MssqlComposeFile {
    if ($script:MssqlMode -eq "local") {
        $script:DbComposeFiles["mssql"] = $MssqlLocalCompose
    } else {
        $script:DbComposeFiles["mssql"] = $MssqlRemoteCompose
    }
}

function Ensure-Command {
    param([string]$Cmd)
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) {
        Log-Error "El comando '$Cmd' es requerido"
        exit 1
    }
}

function Detect-Compose {
    $script:ComposeCmd = @()
    try {
        $null = & docker compose version 2>&1
        $script:ComposeCmd = @("docker", "compose")
    } catch {
        if (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
            $script:ComposeCmd = @("docker-compose")
        } else {
            Log-Error "Docker Compose no está disponible"
            exit 1
        }
    }
}

function Read-EnvValue {
    param(
        [string]$File,
        [string]$Key,
        [string]$Default
    )
    if (-not (Test-Path $File)) {
        return $Default
    }
    $content = Get-Content $File -ErrorAction SilentlyContinue
    foreach ($line in $content) {
        if ($line -match "^$Key=(.*)$") {
            $value = $matches[1]
            $value = $value -replace '^\s*"?|"?\s*$', ''
            $value = $value.Trim()
            return $value
        }
    }
    return $Default
}

function Is-RemoteMssql {
    $host_ = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_REMOTE_HOST" -Default ""
    return (-not [string]::IsNullOrEmpty($host_))
}

function Run-RemoteMssqlInit {
    $host_ = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_REMOTE_HOST" -Default ""
    $port = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_REMOTE_PORT" -Default "15433"
    $pass = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_REMOTE_PASS" -Default "YourStrong@Passw0rd1"
    
    if ([string]::IsNullOrEmpty($host_)) {
        Log-Error "MSSQL_REMOTE_HOST no está definido en $ComposeEnvFile"
        exit 1
    }
    
    Ensure-Command "sqlcmd"
    $server = "$host_,$port"
    Log-Info "Inicializando MSSQL remoto en $server"
    
    $initDir = Join-Path $InfraDbDir "mssql\init"
    if (Test-Path $initDir) {
        Get-ChildItem -Path $initDir -Filter "*.sql" | Sort-Object Name | ForEach-Object {
            Log-Info "Ejecutando $($_.Name) en instancia remota"
            & sqlcmd -C -S $server -U sa -P $pass -i $_.FullName
        }
    }
    
    $seedFile = Join-Path $ProjectRoot "data\out\mssql_data.sql"
    if (Test-Path $seedFile) {
        Log-Info "Ejecutando seed $(Split-Path -Leaf $seedFile)"
        & sqlcmd -C -S $server -U sa -P $pass -i $seedFile
    } else {
        Log-Info "Seed mssql_data.sql no encontrado, se omite"
    }
}

function Configure-MssqlBackendEnv {
    $envFile = Get-BackendEnvFile -Stack "mssql"
    if ([string]::IsNullOrEmpty($envFile)) {
        Log-Warn "No se encontró archivo .env para backend mssql"
        return
    }

    $user = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_USER" -Default "sa"
    $db = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_SALES_DB" -Default "DB_SALES"

    if ($script:MssqlMode -eq "local") {
        $host_ = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_LOCAL_HOST" -Default "localhost"
        $port = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_LOCAL_PORT" -Default "1433"
        $pass = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_LOCAL_PASS" -Default "YourStrong@Passw0rd1"
        $modeLabel = "local"
    } else {
        $host_ = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_REMOTE_HOST" -Default ""
        $port = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_REMOTE_PORT" -Default "15433"
        $pass = Read-EnvValue -File $ComposeEnvFile -Key "MSSQL_REMOTE_PASS" -Default "YourStrong@Passw0rd1"
        $modeLabel = "remota"
    }

    if ([string]::IsNullOrEmpty($host_)) {
        Log-Error "No hay host configurado para MSSQL ($($script:MssqlMode)) en $ComposeEnvFile"
        exit 1
    }

    $url = "sqlserver://${host_}:${port};database=${db};user=${user};password=${pass};encrypt=true;trustServerCertificate=true"

    $content = Get-Content $envFile -Raw -ErrorAction SilentlyContinue
    if ($content -match "^DATABASE_URL=") {
        $content = $content -replace "(?m)^DATABASE_URL=.*$", "DATABASE_URL=`"$url`""
        Set-Content -Path $envFile -Value $content -NoNewline
    } else {
        Add-Content -Path $envFile -Value "DATABASE_URL=`"$url`""
    }

    Log-Info "DATABASE_URL del backend mssql configurada para instancia $modeLabel"
}

function Maybe-ConfigureBackendEnv {
    param([string]$Stack)
    if ($Stack -eq "mssql") {
        Configure-MssqlBackendEnv
    }
}

function Get-BackendEnvFile {
    param([string]$Stack)
    $base = $BackendPaths[$Stack]
    $envLocal = Join-Path $base ".env.local"
    $envFile = Join-Path $base ".env"
    if (Test-Path $envLocal) {
        return $envLocal
    } elseif (Test-Path $envFile) {
        return $envFile
    }
    return ""
}

function Get-FrontendEnvFile {
    param([string]$Stack)
    $base = $FrontendPaths[$Stack]
    $envLocal = Join-Path $base ".env.local"
    $envFile = Join-Path $base ".env"
    if (Test-Path $envLocal) {
        return $envLocal
    } elseif (Test-Path $envFile) {
        return $envFile
    }
    return ""
}

function Resolve-BackendPort {
    param([string]$Stack)
    $envFile = Get-BackendEnvFile -Stack $Stack
    return Read-EnvValue -File $envFile -Key "PORT" -Default $BackendPortDefaults[$Stack]
}

function Resolve-FrontendPort {
    param([string]$Stack)
    $envFile = Get-FrontendEnvFile -Stack $Stack
    return Read-EnvValue -File $envFile -Key "PORT" -Default $FrontendPortDefaults[$Stack]
}

function Ensure-Network {
    $network = "sales_net"
    $exists = & docker network ls --format "{{.Name}}" | Where-Object { $_ -eq $network }
    if (-not $exists) {
        Log-Info "Creando red Docker '$network'"
        & docker network create $network | Out-Null
    }
}

function Sync-UvDependencies {
    param(
        [string]$Stack,
        [string]$Path
    )
    Log-Info "Sincronizando dependencias uv para backend $Stack"
    Push-Location $Path
    try {
        & uv sync
    } finally {
        Pop-Location
    }
}

function Install-BunDependencies {
    param(
        [string]$Role,
        [string]$Stack,
        [string]$Path
    )
    $packageJson = Join-Path $Path "package.json"
    if (-not (Test-Path $packageJson)) {
        Log-Warn "No se encontró package.json para $Role $Stack, se omite bun install"
        return
    }
    Log-Info "Instalando dependencias bun para $Role $Stack"
    Push-Location $Path
    try {
        & bun install
    } finally {
        Pop-Location
    }
}

function Install-PnpmDependencies {
    param(
        [string]$Role,
        [string]$Stack,
        [string]$Path
    )
    $packageJson = Join-Path $Path "package.json"
    if (-not (Test-Path $packageJson)) {
        Log-Warn "No se encontró package.json para $Role $Stack, se omite pnpm install"
        return
    }
    Log-Info "Instalando dependencias pnpm para $Role $Stack"
    Push-Location $Path
    try {
        & pnpm install
    } finally {
        Pop-Location
    }
}

function Start-Database {
    param(
        [string]$Stack,
        [bool]$InitFlag
    )
    $composeFile = $script:DbComposeFiles[$Stack]

    if ($Stack -eq "mssql") {
        if ($script:MssqlMode -eq "remote" -and -not $InitFlag) {
            Log-Info "Stack mssql usa instancia remota; se omite despliegue local"
            return
        }
    }

    if ($Stack -eq "supabase" -and -not $InitFlag) {
        Log-Info "Stack supabase usa instancia remota; se omite despliegue local"
        return
    }

    if ([string]::IsNullOrEmpty($composeFile)) {
        Log-Info "Stack $Stack no tiene base de datos local que levantar"
        return
    }

    if (-not (Test-Path $composeFile)) {
        Log-Error "No se encontró el compose de $Stack en $composeFile"
        exit 1
    }

    Ensure-Network

    if ($InitFlag) {
        Log-Info "Reinicializando base de datos $Stack"
        & $script:ComposeCmd[0] @($script:ComposeCmd[1..($script:ComposeCmd.Length-1)]) -f $composeFile --env-file $ComposeEnvFile down --volumes --remove-orphans 2>&1 | Out-Null
        & $script:ComposeCmd[0] @($script:ComposeCmd[1..($script:ComposeCmd.Length-1)]) -f $composeFile --env-file $ComposeEnvFile --profile init up -d
    } else {
        Log-Info "Levantando base de datos $Stack"
        & $script:ComposeCmd[0] @($script:ComposeCmd[1..($script:ComposeCmd.Length-1)]) -f $composeFile --env-file $ComposeEnvFile up -d
    }
}

function Wait-ForInitContainer {
    param([string]$Stack)
    
    $containerName = ""
    switch ($Stack) {
        "mssql" {
            if ($script:MssqlMode -eq "local") {
                $containerName = $MssqlInitContainerLocal
            } else {
                $containerName = $MssqlInitContainerRemote
            }
        }
        "mysql" { $containerName = "mysql_sales_init" }
        "mongo" { $containerName = "mongo_sales_init" }
        "neo4j" { $containerName = "neo4j_sales_init" }
        "supabase" { $containerName = $SupabaseInitContainer }
        default { return }
    }

    $containerExists = & docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $containerName }
    if (-not $containerExists) {
        Log-Info "Contenedor de init $containerName no encontrado, continuando..."
        return
    }

    Log-Info "Esperando a que termine la inicialización de $Stack..."
    $maxWait = $InitMaxWait[$Stack]
    $unlimited = $maxWait -le 0
    $waited = 0
    $interval = 5

    while ($true) {
        $status = & docker inspect -f "{{.State.Status}}" $containerName 2>&1
        if ($LASTEXITCODE -ne 0) {
            $status = "not_found"
        }

        switch ($status) {
            "exited" {
                $exitCode = & docker inspect -f "{{.State.ExitCode}}" $containerName 2>&1
                if ($exitCode -eq "0") {
                    Log-Info "Inicialización de $Stack completada exitosamente"
                    return
                } else {
                    Log-Error "Inicialización de $Stack falló (exit code: $exitCode)"
                    Log-Info "Revisa los logs con: docker logs $containerName"
                    return
                }
            }
            "running" {
                Start-Sleep -Seconds $interval
                $waited += $interval
                Log-Info "Inicialización de $Stack en progreso... (${waited}s)"
            }
            "not_found" {
                Log-Info "Contenedor de init no encontrado, continuando..."
                return
            }
            default {
                Start-Sleep -Seconds $interval
                $waited += $interval
            }
        }

        if (-not $unlimited -and $waited -ge $maxWait) {
            Log-Error "Timeout esperando inicialización de $Stack (${maxWait}s)"
            Log-Info "Puedes revisar los logs con: docker logs $containerName"
            return
        }
    }
}

function Stop-Database {
    param([string]$Stack)
    $composeFile = $script:DbComposeFiles[$Stack]
    if (-not [string]::IsNullOrEmpty($composeFile) -and (Test-Path $composeFile)) {
        Log-Info "Deteniendo base de datos $Stack"
        & $script:ComposeCmd[0] @($script:ComposeCmd[1..($script:ComposeCmd.Length-1)]) -f $composeFile --env-file $ComposeEnvFile down --remove-orphans 2>&1 | Out-Null
    } else {
        Log-Info "Stack $Stack no tiene base de datos local que detener"
    }
}

function Start-ProcessBackground {
    param(
        [string]$Name,
        [string]$WorkDir,
        [string]$Cmd
    )
    $pidFile = Join-Path $PidDir "$Name.pid"
    $logFile = Join-Path $LogDir "$Name.log"

    if (Test-Path $pidFile) {
        $existingPid = Get-Content $pidFile
        try {
            $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
            if ($proc) {
                Log-Info "$Name ya se está ejecutando (PID $existingPid)"
                return
            }
        } catch {}
    }

    "" | Out-File -FilePath $logFile -Force

    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = "cmd.exe"
    $processInfo.Arguments = "/c cd /d `"$WorkDir`" && $Cmd >> `"$logFile`" 2>&1"
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true
    $processInfo.RedirectStandardOutput = $false
    $processInfo.RedirectStandardError = $false
    $processInfo.WorkingDirectory = $WorkDir

    $process = [System.Diagnostics.Process]::Start($processInfo)
    $process.Id | Out-File -FilePath $pidFile -Force

    Log-Info "$Name iniciado (PID $($process.Id))"
}

function Stop-ProcessBackground {
    param([string]$Name)
    $pidFile = Join-Path $PidDir "$Name.pid"
    if (-not (Test-Path $pidFile)) {
        Log-Warn "No hay PID registrado para $Name"
        return
    }
    $pid = Get-Content $pidFile
    try {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Log-Info "Deteniendo $Name (PID $pid)"
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        } else {
            Log-Warn "$Name no está ejecutándose"
        }
    } catch {
        Log-Warn "$Name no está ejecutándose"
    }
    Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
}

function Start-Backend {
    param([string]$Stack)
    $path = $BackendPaths[$Stack]
    $runner = $BackendRunners[$Stack]
    $port = Resolve-BackendPort -Stack $Stack

    if (-not (Test-Path $path)) {
        Log-Error "No existe backend para $Stack"
        exit 1
    }

    Maybe-ConfigureBackendEnv -Stack $Stack

    switch ($runner) {
        "bun" {
            Ensure-Command "bun"
            Install-BunDependencies -Role "backend" -Stack $Stack -Path $path
            $cmd = "set PORT=$port && bun run dev"
            Start-ProcessBackground -Name "backend-$Stack" -WorkDir $path -Cmd $cmd
        }
        "pnpm" {
            Ensure-Command "pnpm"
            $cmd = "set PORT=$port && pnpm run dev"
            Start-ProcessBackground -Name "backend-$Stack" -WorkDir $path -Cmd $cmd
        }
        "uv" {
            Ensure-Command "uv"
            Sync-UvDependencies -Stack $Stack -Path $path
            $cmd = "set PORT=$port && uv run dev"
            Start-ProcessBackground -Name "backend-$Stack" -WorkDir $path -Cmd $cmd
        }
        default {
            Log-Error "Runner desconocido para backend $Stack"
            exit 1
        }
    }
}

function Start-Frontend {
    param([string]$Stack)
    $path = $FrontendPaths[$Stack]
    $runner = $FrontendRunners[$Stack]
    $port = Resolve-FrontendPort -Stack $Stack

    if (-not (Test-Path $path)) {
        Log-Error "No existe frontend para $Stack"
        exit 1
    }

    switch ($runner) {
        "bun" {
            Ensure-Command "bun"
            Install-BunDependencies -Role "frontend" -Stack $Stack -Path $path
            $cmd = "set PORT=$port && bun run dev"
            Start-ProcessBackground -Name "frontend-$Stack" -WorkDir $path -Cmd $cmd
        }
        "pnpm" {
            Ensure-Command "pnpm"
            Install-PnpmDependencies -Role "frontend" -Stack $Stack -Path $path
            $cmd = "set PORT=$port && pnpm run dev"
            Start-ProcessBackground -Name "frontend-$Stack" -WorkDir $path -Cmd $cmd
        }
        default {
            Log-Error "Runner desconocido para frontend $Stack"
            exit 1
        }
    }
}

function Stop-StackProcesses {
    param([string]$Stack)
    Stop-ProcessBackground -Name "frontend-$Stack"
    Stop-ProcessBackground -Name "backend-$Stack"
}

function Run-PrismaTasks {
    param([string]$Stack)
    $path = $BackendPaths[$Stack]
    if ($Stack -ne "mssql" -and $Stack -ne "mysql") {
        return
    }
    Maybe-ConfigureBackendEnv -Stack $Stack
    Ensure-Command "bun"
    $packageJson = Join-Path $path "package.json"
    if (-not (Test-Path $packageJson)) {
        Log-Warn "No hay package.json en $path para ejecutar Prisma"
        return
    }
    Install-BunDependencies -Role "backend" -Stack $Stack -Path $path
    Log-Info "Ejecutando Prisma generate para $Stack"
    Push-Location $path
    try {
        & bun run db:generate
        $content = Get-Content $packageJson -Raw
        if ($content -match '"db:push"') {
            Log-Info "Ejecutando Prisma db:push para $Stack"
            & bun run db:push
        }
    } finally {
        Pop-Location
    }
}

function Show-SummaryUrls {
    param([string]$Stack)
    $backendPort = Resolve-BackendPort -Stack $Stack
    $frontendPort = Resolve-FrontendPort -Stack $Stack
    Log-Info "Backend $Stack`: http://localhost:$backendPort"
    Log-Info "Frontend $Stack`: http://localhost:$frontendPort"
    Log-Info "Logs backend: $LogDir\backend-$Stack.log"
    Log-Info "Logs frontend: $LogDir\frontend-$Stack.log"
}

function Handle-Up {
    param([string]$Stack)
    Start-Database -Stack $Stack -InitFlag $false
    Start-Backend -Stack $Stack
    Start-Frontend -Stack $Stack
    Show-SummaryUrls -Stack $Stack
}

function Handle-Init {
    param([string]$Stack)
    Stop-StackProcesses -Stack $Stack
    Start-Database -Stack $Stack -InitFlag $true
    Wait-ForInitContainer -Stack $Stack
    if ($Stack -eq "mssql" -or $Stack -eq "mysql") {
        Run-PrismaTasks -Stack $Stack
    }
    Start-Backend -Stack $Stack
    Start-Frontend -Stack $Stack
    Show-SummaryUrls -Stack $Stack
}

function Handle-Down {
    param([string]$Stack)
    Stop-StackProcesses -Stack $Stack
    Stop-Database -Stack $Stack
}

function Parse-Args {
    param([string[]]$Arguments)
    
    $script:Action = ""
    $script:Targets = @()
    $includeAll = $false
    $modeOverride = ""

    for ($i = 0; $i -lt $Arguments.Length; $i++) {
        $arg = $Arguments[$i]
        switch -Regex ($arg) {
            "^(-Up|--up)$" {
                if (-not [string]::IsNullOrEmpty($script:Action)) {
                    Log-Error "Solo se permite una acción por ejecución"
                    exit 1
                }
                $script:Action = "up"
            }
            "^(-Down|--down)$" {
                if (-not [string]::IsNullOrEmpty($script:Action)) {
                    Log-Error "Solo se permite una acción por ejecución"
                    exit 1
                }
                $script:Action = "down"
            }
            "^(-Init|--init)$" {
                if (-not [string]::IsNullOrEmpty($script:Action)) {
                    Log-Error "Solo se permite una acción por ejecución"
                    exit 1
                }
                $script:Action = "init"
            }
            "^(-Local|--local)$" {
                $modeOverride = "local"
                $script:MssqlModeExplicit = $true
            }
            "^(-Remote|--remote)$" {
                $modeOverride = "remote"
                $script:MssqlModeExplicit = $true
            }
            "^all$" {
                $includeAll = $true
            }
            "^(-Help|--help|-h)$" {
                Show-Help
                exit 0
            }
            default {
                $stackList = $arg -split ","
                foreach ($stackItem in $stackList) {
                    if ($stackItem -in @("mssql", "mysql", "mongo", "neo4j", "supabase")) {
                        $script:Targets += $stackItem
                    } else {
                        Log-Error "Argumento no reconocido: $stackItem"
                        Show-Help
                        exit 1
                    }
                }
            }
        }
    }

    if ([string]::IsNullOrEmpty($script:Action)) {
        Log-Error "Debes especificar -Up, -Down o -Init"
        exit 1
    }

    if (-not [string]::IsNullOrEmpty($modeOverride)) {
        $script:MssqlMode = $modeOverride
    }

    if ($script:Action -eq "init" -and -not $script:MssqlModeExplicit) {
        $script:MssqlMode = "remote"
    }

    if ($includeAll) {
        $script:Targets = $Stacks
        if ($script:Action -ne "down") {
            $script:OpenIndexAfter = $true
        }
    } elseif ($script:Targets.Length -eq 0) {
        $script:Targets = $Stacks
    }
}

function Main {
    param([string[]]$Arguments)
    
    Ensure-Command "docker"
    Detect-Compose
    Parse-Args -Arguments $Arguments
    Set-MssqlComposeFile

    foreach ($stack in $script:Targets) {
        if ($stack -notin @("mssql", "mysql", "mongo", "neo4j", "supabase")) {
            Log-Error "Stack desconocido: $stack"
            exit 1
        }
        switch ($script:Action) {
            "up" { Handle-Up -Stack $stack }
            "down" { Handle-Down -Stack $stack }
            "init" { Handle-Init -Stack $stack }
        }
    }

    if ($script:OpenIndexAfter -and $script:Action -ne "down") {
        Open-IndexHtml
    }
}

Main -Arguments $args

