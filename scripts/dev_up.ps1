# ================================================================
# Script de desarrollo para levantar bases de datos
# ProyectoBases2 - IC4302 Bases de datos II
# Versión para PowerShell (Windows)
#
# Uso:
#   .\scripts\dev_up.ps1 [opciones] [bases_de_datos]
#
# Opciones:
#   -Init              Reinicializar las bases de datos (borra datos existentes)
#   -Down              Detener y remover contenedores
#   -Logs              Mostrar logs de los servicios
#   -Help              Mostrar esta ayuda
#
# Bases de datos disponibles:
#   mssql              Microsoft SQL Server
#   mysql              MySQL 8.x
#   neo4j              Neo4j
#   all                Todas las bases de datos (default)
#
# Ejemplos:
#   .\scripts\dev_up.ps1                    # Levantar todas las BD
#   .\scripts\dev_up.ps1 -Init mssql        # Reinicializar solo MSSQL
#   .\scripts\dev_up.ps1 -Down all          # Detener todas las BD
#   .\scripts\dev_up.ps1 -Logs mysql        # Ver logs de MySQL
# ================================================================

param(
    [switch]$Init,
    [switch]$Down,
    [switch]$Logs,
    [switch]$Help,
    [string[]]$Databases
)

$ErrorActionPreference = "Stop"

# ================================================================
# Configuración
# ================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$InfraDir = Join-Path (Join-Path $ProjectRoot "infra") "docker"
$EnvFile = Join-Path $ProjectRoot ".env.local"

# ================================================================
# Colores para output
# ================================================================
$Colors = @{
    Info    = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
}

# ================================================================
# Funciones de utilidad
# ================================================================
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("Info", "Success", "Warning", "Error")]
        [string]$Type = "Info"
    )
    
    $prefix = switch ($Type) {
        "Info"    { "[INF]" }
        "Success" { "[SUC]" }
        "Warning" { "[WAR]" }
        "Error"   { "[ERR]" }
    }
    
    Write-Host "$prefix $Message" -ForegroundColor $Colors[$Type]
}

function Show-Help {
    $helpText = @"
Script de desarrollo para levantar bases de datos
ProyectoBases2 - IC4302 Bases de datos II

Uso:
  .\scripts\dev_up.ps1 [opciones] [bases_de_datos]

Opciones:
  -Up                Levantar las bases de datos (default)
  -Init              Reinicializar las bases de datos (borra datos existentes)
  -Down              Detener y remover contenedores
  -Logs              Mostrar logs de los servicios
  -Help              Mostrar esta ayuda

Bases de datos disponibles:
  mssql              Microsoft SQL Server
  mysql              MySQL 8.x
  neo4j              Neo4j
  all                Todas las bases de datos (default)

Ejemplos:
  .\scripts\dev_up.ps1                    # Levantar todas las BD
  .\scripts\dev_up.ps1 -Init mssql        # Reinicializar solo MSSQL
  .\scripts\dev_up.ps1 -Down all          # Detener todas las BD
  .\scripts\dev_up.ps1 -Logs mysql        # Ver logs de MySQL

Archivos de configuración requeridos:
  - .env.local (variables de entorno)
  - infra\docker\databases\*\compose.yaml
"@
    Write-Host $helpText
}

function Test-Dependencies {
    Write-Log "Verificando dependencias..."
    
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            throw "Docker no está instalado"
        }
        Write-Log "Docker encontrado: $dockerVersion" -Type Success
    }
    catch {
        Write-Log "Docker no está instalado o no está en PATH" -Type Error
        exit 1
    }
    
    try {
        $composeVersion = docker compose version 2>$null
        if (-not $composeVersion) {
            throw "Docker Compose no está disponible"
        }
        Write-Log "Docker Compose encontrado" -Type Success
    }
    catch {
        Write-Log "Docker Compose no está disponible" -Type Error
        exit 1
    }
}

function Test-Files {
    Write-Log "Verificando archivos requeridos..."
    
    if (-not (Test-Path $EnvFile)) {
        Write-Log "Archivo .env.local no encontrado en $EnvFile" -Type Error
        Write-Log "Crea el archivo basado en .env.example" -Type Info
        exit 1
    }
    
    Write-Log "Archivos encontrados" -Type Success
}

function Invoke-DockerCompose {
    param(
        [string]$Database,
        [string]$Action
    )
    
    $composeFile = "$InfraDir/databases/$Database/compose.yaml"
    
    if (-not (Test-Path $composeFile)) {
        Write-Log "Archivo compose.yaml no encontrado para $Database`: $composeFile" -Type Warning
        return $false
    }
    
    Write-Log "Ejecutando: docker compose -f $composeFile --env-file $EnvFile $Action" -Type Info

    $cmd = "docker compose -f `"$composeFile`" --env-file `"$EnvFile`" $Action"
    Start-Sleep -Seconds 3

    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = "cmd.exe"
    $processInfo.Arguments = "/c $cmd"
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    $process.Start() | Out-Null
    $output = $process.StandardOutput.ReadToEnd() + $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    $exitCode = $process.ExitCode

    if ($exitCode -eq 0 -or ($output -match "Running|Up|done|Created")) {
        Write-Log "Operación completada para $Database" -Type Success
        return $true
    } else {
        Write-Log "Error en operación para $Database`: $output" -Type Error
        return $false
    }
}





function Start-Services {
    param(
        [string]$Database,
        [bool]$InitFlag
    )
    
    if ($InitFlag) {
        Write-Log "Levantando $Database con inicialización..." -Type Info
        Invoke-DockerCompose -Database $Database -Action "--profile init up -d"
    }
    else {
        Write-Log "Levantando $Database..." -Type Info
        Invoke-DockerCompose -Database $Database -Action "up -d"
    }
}

function Stop-Services {
    param(
        [string]$Database
    )
    
    Write-Log "Deteniendo $Database..." -Type Info
    Invoke-DockerCompose -Database $Database -Action "down --volumes --remove-orphans"
}

function Show-Logs {
    param(
        [string]$Database
    )
    
    Write-Log "Mostrando logs de $Database..." -Type Info
    Invoke-DockerCompose -Database $Database -Action "logs -f"
}

# ================================================================
# Función principal
# ================================================================
function Main {
    # Mostrar ayuda si se solicita
    if ($Help) {
        Show-Help
        exit 0
    }
    
    # Si no se especificaron bases de datos, usar todas
    if ($Databases.Count -eq 0) {
        $Databases = @("mssql", "mysql", "neo4j")
    }
    else {
        # Procesar "all"
        if ($Databases -contains "all") {
            $Databases = @("mssql", "mysql", "neo4j")
        }
    }
    
    # Verificaciones iniciales
    Test-Dependencies
    Test-Files
    
    # Cambiar al directorio del proyecto
    Push-Location $ProjectRoot
    
    try {
        # Ejecutar acciones
        $errors = 0
        
        foreach ($db in $Databases) {
            if ($Down) {
                if (-not (Stop-Services -Database $db)) {
                    $errors++
                }
            }
            elseif ($Logs) {
                if (-not (Show-Logs -Database $db)) {
                    $errors++
                }
            }
            else {
                # --Up o comportamiento por defecto levantan servicios
                if (-not (Start-Services -Database $db -InitFlag $Init)) {
                    $errors++
                }
            }
        }
        
        # Resumen final
        if ($errors -eq 0) {
            if ($Down) {
                Write-Log "Todas las bases de datos detenidas correctamente" -Type Success
            }
            elseif ($Logs) {
                Write-Log "Logs mostrados" -Type Success
            }
            else {
                if ($Init) {
                    Write-Log "Bases de datos reinicializadas: $($Databases -join ', ')" -Type Success
                }
                else {
                    Write-Log "Bases de datos levantadas: $($Databases -join ', ')" -Type Success
                }
            }
        }
        else {
            Write-Log "$errors errores encontrados" -Type Error
            exit 1
        }
    }
    finally {
        Pop-Location
    }
}

# ================================================================
# Ejecutar función principal
# ================================================================
Main
