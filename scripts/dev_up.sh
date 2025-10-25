#!/bin/bash
# ================================================================
# Script de desarrollo para levantar bases de datos
# ProyectoBases2 - IC4302 Bases de datos II
#
# Uso:
#   ./scripts/dev_up.sh [opciones] [bases_de_datos]
#
# Opciones:
#   --init     Reinicializar las bases de datos (borra datos existentes)
#   --down     Detener y remover contenedores
#   --logs     Mostrar logs de los servicios
#   --help     Mostrar esta ayuda
#
# Bases de datos disponibles:
#   mssql      Microsoft SQL Server
#   mysql      MySQL 8.x
#   mongo      MongoDB
#   neo4j      Neo4j
#   all        Todas las bases de datos (default)
#
# Ejemplos:
#   ./scripts/dev_up.sh                    # Levantar todas las BD
#   ./scripts/dev_up.sh --init mssql       # Reinicializar solo MSSQL
#   ./scripts/dev_up.sh --down all         # Detener todas las BD
#   ./scripts/dev_up.sh --logs mysql       # Ver logs de MySQL
# ================================================================

set -euo pipefail

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_ROOT/infra/docker"
ENV_FILE="$PROJECT_ROOT/.env.local"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de utilidad
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Script de desarrollo para levantar bases de datos
ProyectoBases2 - IC4302 Bases de datos II

Uso:
  ./scripts/dev_up.sh [opciones] [bases_de_datos]

Opciones:
  --up       Levantar las bases de datos (default)
  --init     Reinicializar las bases de datos (borra datos existentes)
  --down     Detener y remover contenedores
  --logs     Mostrar logs de los servicios
  --help     Mostrar esta ayuda

Bases de datos disponibles:
  mssql      Microsoft SQL Server
  mysql      MySQL 8.x
  mongo      MongoDB
  neo4j      Neo4j
  all        Todas las bases de datos (default)

Ejemplos:
  ./scripts/dev_up.sh                    # Levantar todas las BD
  ./scripts/dev_up.sh --up all           # Levantar todas las BD (explícito)
  ./scripts/dev_up.sh --up mssql         # Levantar solo MSSQL
  ./scripts/dev_up.sh --init mssql       # Reinicializar solo MSSQL
  ./scripts/dev_up.sh --down all         # Detener todas las BD
  ./scripts/dev_up.sh --logs mysql       # Ver logs de MySQL

Archivos de configuración requeridos:
  - .env.local (variables de entorno)
  - infra/docker/databases/*/compose.yaml
EOF
}

# Verificar dependencias
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado o no está en PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose no está disponible"
        exit 1
    fi
}

# Verificar archivos requeridos
check_files() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Archivo .env.local no encontrado en $ENV_FILE"
        log_info "Crea el archivo basado en .env.example"
        exit 1
    fi
}

# Función para ejecutar docker compose
run_compose() {
    local db=$1
    local action=$2
    local compose_file="$INFRA_DIR/databases/$db/compose.yaml"

    if [[ ! -f "$compose_file" ]]; then
        log_warning "Archivo compose.yaml no encontrado para $db: $compose_file"
        return 1
    fi

    log_info "Ejecutando: docker compose -f $compose_file --env-file $ENV_FILE $action"

    if docker compose -f "$compose_file" --env-file "$ENV_FILE" $action; then
        log_success "Operación completada para $db"
        return 0
    else
        log_error "Error en operación para $db"
        return 1
    fi
}

# Levantar servicios
up_services() {
    local db=$1
    local init=$2

    if [[ "$init" == "true" ]]; then
        log_info "Levantando $db con inicialización..."
        run_compose "$db" "--profile init up -d"
    else
        log_info "Levantando $db..."
        run_compose "$db" "up -d"
    fi
}

# Detener servicios
down_services() {
    local db=$1

    log_info "Deteniendo $db..."
    run_compose "$db" "down --volumes --remove-orphans"
}

# Mostrar logs
show_logs() {
    local db=$1

    log_info "Mostrando logs de $db..."
    run_compose "$db" "logs -f"
}

# Función principal
main() {
    local init=false
    local up=false
    local down=false
    local logs=false
    local databases=()

    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --init)
                init=true
                shift
                ;;
            --up)
                up=true
                shift
                ;;
            --down)
                down=true
                shift
                ;;
            --logs)
                logs=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            mssql|mysql|mongo|neo4j)
                databases+=("$1")
                shift
                ;;
            all)
                databases=(mssql mysql mongo neo4j)
                shift
                ;;
            *)
                log_error "Opción desconocida: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Si no se especificaron bases de datos, usar todas
    if [[ ${#databases[@]} -eq 0 ]]; then
        databases=(mssql mysql mongo neo4j)
    fi

    # Verificaciones iniciales
    check_dependencies
    check_files

    # Cambiar al directorio del proyecto
    cd "$PROJECT_ROOT"

    # Ejecutar acciones
    local errors=0
    for db in "${databases[@]}"; do
        if [[ "$down" == "true" ]]; then
            if ! down_services "$db"; then
                ((errors++))
            fi
        elif [[ "$logs" == "true" ]]; then
            if ! show_logs "$db"; then
                ((errors++))
            fi
        else
            # --up o comportamiento por defecto levantan servicios
            if ! up_services "$db" "$init"; then
                ((errors++))
            fi
        fi
    done

    # Resumen final
    if [[ $errors -eq 0 ]]; then
        if [[ "$down" == "true" ]]; then
            log_success "Todas las bases de datos detenidas correctamente"
        elif [[ "$logs" == "true" ]]; then
            log_success "Logs mostrados"
        else
            local action_msg="levantadas"
            if [[ "$init" == "true" ]]; then
                action_msg="reinicializadas"
            fi
            log_success "Bases de datos $action_msg: ${databases[*]}"
        fi
    else
        log_error "$errors errores encontrados"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"