#!/bin/bash
# ================================================================
# Script de desarrollo para levantar backends y frontends
# ProyectoBases2 - IC4302 Bases de datos II
#
# Uso:
#   ./scripts/dev_apps.sh --up [base_de_datos]
#   ./scripts/dev_apps.sh --down [base_de_datos]
#
# Bases de datos disponibles:
#   mssql      Microsoft SQL Server + api-mssql + web-mssql
#   mysql      MySQL 8.x + api-mysql + web-mysql
#   mongo      MongoDB + api-mongo + web-mongo
#   neo4j      Neo4j + api-neo4j + web-neo4j
#   supabase   Supabase + api-supabase + web-supabase
#
# Ejemplos:
#   ./scripts/dev_apps.sh --up mssql      # Levantar MSSQL, API y frontend
#   ./scripts/dev_apps.sh --down mssql    # Detener MSSQL, API y frontend
#   ./scripts/dev_apps.sh --up mysql      # Levantar MySQL, API y frontend
#
# ================================================================

set -euo pipefail

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funciones de utilidad
log_info() {
    echo -e "${BLUE}[INF]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUC]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WAR]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERR]${NC} $1"
}

log_header() {
    echo -e "${CYAN}$1${NC}"
}

show_help() {
    cat << EOF
Script de desarrollo para levantar backends y frontends
ProyectoBases2 - IC4302 Bases de datos II

Uso:
  ./scripts/dev_apps.sh --up [base_de_datos]
  ./scripts/dev_apps.sh --down [base_de_datos]
  ./scripts/dev_apps.sh --help

Opciones:
  --up       Levantar backend (API) y frontend (modo desarrollador)
  --down     Detener backend y frontend
  --help     Mostrar esta ayuda

Bases de datos disponibles:
  mssql      Microsoft SQL Server + api-mssql + web-mssql
  mysql      MySQL 8.x + api-mysql + web-mysql
  mongo      MongoDB + api-mongo + web-mongo
  neo4j      Neo4j + api-neo4j + web-neo4j
  supabase   Supabase + api-supabase + web-supabase

Ejemplos:
  ./scripts/dev_apps.sh --up mssql       # Levantar MSSQL app stack
  ./scripts/dev_apps.sh --down mssql     # Detener MSSQL app stack
  ./scripts/dev_apps.sh --up mysql       # Levantar MySQL app stack

Archivos de configuración requeridos:
  - package.json con scripts dev/start
  - services/api-*/package.json
  - apps/web-*/package.json
EOF
}

# Verificar dependencias
check_dependencies() {
    if ! command -v pnpm &> /dev/null; then
        log_error "pnpm no está instalado o no está en PATH"
        exit 1
    fi

    if ! command -v lsof &> /dev/null; then
        log_warning "lsof no está instalado. Algunos comandos podrían no funcionar correctamente"
    fi
}

# Validar base de datos
validate_database() {
    local db=$1
    case $db in
        mssql|mysql|mongo|neo4j|supabase)
            return 0
            ;;
        *)
            log_error "Base de datos desconocida: $db"
            log_info "Bases de datos disponibles: mssql, mysql, mongo, neo4j, supabase"
            return 1
            ;;
    esac
}

# Obtener rutas de servicios
get_service_paths() {
    local db=$1
    local api_path="$PROJECT_ROOT/services/api-$db"
    local web_path="$PROJECT_ROOT/apps/web-$db"

    if [[ ! -d "$api_path" ]]; then
        log_error "Directorio de API no encontrado: $api_path"
        return 1
    fi

    if [[ ! -d "$web_path" ]]; then
        log_error "Directorio de frontend no encontrado: $web_path"
        return 1
    fi

    echo "$api_path:$web_path"
}

# Levantar servicios
up_services() {
    local db=$1
    local paths
    local api_path
    local web_path

    if ! paths=$(get_service_paths "$db"); then
        return 1
    fi

    IFS=':' read -r api_path web_path <<< "$paths"

    log_header "=========================================="
    log_header "Levantando $db (API + Frontend)"
    log_header "=========================================="

    # Cambiar al directorio del proyecto
    cd "$PROJECT_ROOT"

    # Instalar dependencias si es necesario
    if [[ ! -d "node_modules" ]] || [[ ! -d "$api_path/node_modules" ]] || [[ ! -d "$web_path/node_modules" ]]; then
        log_info "Instalando dependencias..."
        pnpm install
    fi

    # Levantar API
    log_info "Levantando API (services/api-$db)..."
    cd "$api_path"
    
    # Detectar si usa bun o node
    if grep -q '"scripts"' package.json && grep -q '"dev"' package.json; then
        # Ejecutar en background
        if grep -q "bun" package.json || [[ -f "bunfig.toml" ]]; then
            log_info "Iniciando API con bun..."
            bun run dev > "$PROJECT_ROOT/.dev_logs/api-$db.log" 2>&1 &
        else
            log_info "Iniciando API con pnpm..."
            pnpm dev > "$PROJECT_ROOT/.dev_logs/api-$db.log" 2>&1 &
        fi
        local api_pid=$!
        echo "$api_pid" > "$PROJECT_ROOT/.dev_pids/api-$db.pid"
        log_success "API iniciada (PID: $api_pid)"
        sleep 2
    else
        log_warning "No se encontró script 'dev' en $api_path/package.json"
        return 1
    fi

    # Levantar Frontend
    log_info "Levantando Frontend (apps/web-$db)..."
    cd "$web_path"

    if grep -q '"scripts"' package.json && grep -q '"dev"' package.json; then
        # Detectar si bun está disponible y usar para frontend también
        if command -v bun &> /dev/null; then
            log_info "Iniciando Frontend con bun..."
            bun run dev > "$PROJECT_ROOT/.dev_logs/web-$db.log" 2>&1 &
        else
            log_info "Iniciando Frontend con pnpm..."
            pnpm dev > "$PROJECT_ROOT/.dev_logs/web-$db.log" 2>&1 &
        fi
        local web_pid=$!
        echo "$web_pid" > "$PROJECT_ROOT/.dev_pids/web-$db.pid"
        log_success "Frontend iniciado (PID: $web_pid)"
    else
        log_warning "No se encontró script 'dev' en $web_path/package.json"
        return 1
    fi

    cd "$PROJECT_ROOT"
    log_header "=========================================="
    log_success "Stack de $db levantado correctamente"
    log_header "=========================================="
    
    # Mostrar URLs de acceso
    log_info ""
    log_info "📍 Direcciones de acceso:"
    log_info ""
    
    # Detectar puertos
    local api_port=${API_PORT:-3000}
    local web_port=${WEB_PORT:-5173}
    
    case $db in
        mssql)
            log_info "  🔵 Backend (API MSSQL):  http://localhost:$api_port"
            log_info "  🔵 Swagger UI:           http://localhost:$api_port/ui"
            log_info "  🔵 Frontend MSSQL:       http://localhost:$web_port"
            ;;
        mysql)
            log_info "  🟡 Backend (API MySQL):  http://localhost:$api_port"
            log_info "  🟡 Swagger UI:           http://localhost:$api_port/ui"
            log_info "  🟡 Frontend MySQL:       http://localhost:$web_port"
            ;;
        mongo)
            log_info "  🟢 Backend (API Mongo):  http://localhost:$api_port"
            log_info "  🟢 Swagger UI:           http://localhost:$api_port/ui"
            log_info "  🟢 Frontend Mongo:       http://localhost:$web_port"
            ;;
        neo4j)
            log_info "  🔴 Backend (API Neo4j):  http://localhost:$api_port"
            log_info "  🔴 Swagger UI:           http://localhost:$api_port/ui"
            log_info "  🔴 Frontend Neo4j:       http://localhost:$web_port"
            ;;
        supabase)
            log_info "  🟣 Backend (API Supabase): http://localhost:$api_port"
            log_info "  🟣 Swagger UI:            http://localhost:$api_port/ui"
            log_info "  🟣 Frontend Supabase:     http://localhost:$web_port"
            ;;
    esac
    
    log_info ""
    log_info "📋 Logs:"
    log_info "  API logs:  $PROJECT_ROOT/.dev_logs/api-$db.log"
    log_info "  Web logs:  $PROJECT_ROOT/.dev_logs/web-$db.log"
    log_info ""
    log_info "⏹️  Para detener: ./scripts/dev_apps.sh --down $db"
}

# Detener servicios
down_services() {
    local db=$1
    local api_pid_file="$PROJECT_ROOT/.dev_pids/api-$db.pid"
    local web_pid_file="$PROJECT_ROOT/.dev_pids/web-$db.pid"

    log_header "=========================================="
    log_header "Deteniendo $db (API + Frontend)"
    log_header "=========================================="

    local stopped=0

    # Detener API
    if [[ -f "$api_pid_file" ]]; then
        local api_pid=$(cat "$api_pid_file")
        if kill -0 "$api_pid" 2>/dev/null; then
            log_info "Deteniendo API (PID: $api_pid)..."
            kill "$api_pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$api_pid" 2>/dev/null; then
                log_warning "Forzando cierre de API..."
                kill -9 "$api_pid" 2>/dev/null || true
            fi
            log_success "API detenida"
            ((stopped++))
        else
            log_warning "Proceso API (PID: $api_pid) no encontrado"
        fi
        rm -f "$api_pid_file"
    else
        log_warning "Archivo PID de API no encontrado: $api_pid_file"
    fi

    # Detener Frontend
    if [[ -f "$web_pid_file" ]]; then
        local web_pid=$(cat "$web_pid_file")
        if kill -0 "$web_pid" 2>/dev/null; then
            log_info "Deteniendo Frontend (PID: $web_pid)..."
            kill "$web_pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$web_pid" 2>/dev/null; then
                log_warning "Forzando cierre de Frontend..."
                kill -9 "$web_pid" 2>/dev/null || true
            fi
            log_success "Frontend detenido"
            ((stopped++))
        else
            log_warning "Proceso Frontend (PID: $web_pid) no encontrado"
        fi
        rm -f "$web_pid_file"
    else
        log_warning "Archivo PID de Frontend no encontrado: $web_pid_file"
    fi

    log_header "=========================================="
    if [[ $stopped -gt 0 ]]; then
        log_success "Stack de $db detenido correctamente"
    else
        log_warning "No se encontraron procesos para detener"
    fi
    log_header "=========================================="
}

# Función principal
main() {
    local action=""
    local database=""

    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --up)
                action="up"
                shift
                ;;
            --down)
                action="down"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            mssql|mysql|mongo|neo4j|supabase)
                database="$1"
                shift
                ;;
            *)
                log_error "Opción desconocida: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Validar argumentos
    if [[ -z "$action" ]]; then
        log_error "Debes especificar una acción: --up o --down"
        show_help
        exit 1
    fi

    if [[ -z "$database" ]]; then
        log_error "Debes especificar una base de datos"
        show_help
        exit 1
    fi

    # Validar base de datos
    if ! validate_database "$database"; then
        exit 1
    fi

    # Verificar dependencias
    check_dependencies

    # Crear directorios para logs y PIDs
    mkdir -p "$PROJECT_ROOT/.dev_logs"
    mkdir -p "$PROJECT_ROOT/.dev_pids"

    # Ejecutar acción
    case $action in
        up)
            if ! up_services "$database"; then
                exit 1
            fi
            ;;
        down)
            if ! down_services "$database"; then
                exit 1
            fi
            ;;
    esac
}

# Ejecutar función principal
main "$@"
