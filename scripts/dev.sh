
#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DB_DIR="$PROJECT_ROOT/infra/docker/databases"

STATE_DIR="$PROJECT_ROOT/.dev_runtime"
PID_DIR="$STATE_DIR/pids"
LOG_DIR="$STATE_DIR/logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

COMPOSE_ENV_FILE=""
if [[ -f "$PROJECT_ROOT/.env.local" ]]; then
	COMPOSE_ENV_FILE="$PROJECT_ROOT/.env.local"
elif [[ -f "$PROJECT_ROOT/.env" ]]; then
	COMPOSE_ENV_FILE="$PROJECT_ROOT/.env"
else
	echo "[err] No se encontró .env.local ni .env en la raíz del proyecto" >&2
	exit 1
fi

STACKS=(mssql mysql mongo neo4j supabase)

declare -A DB_COMPOSE_FILES=(
	[mssql]="$INFRA_DB_DIR/mssql/compose.yaml"
	[mysql]="$INFRA_DB_DIR/mysql/compose.yaml"
	[mongo]="$INFRA_DB_DIR/mongo/compose.yaml"
	[neo4j]="$INFRA_DB_DIR/neo4j/compose.yaml"
	[supabase]=""
)

declare -A BACKEND_PATHS=(
	[mssql]="$PROJECT_ROOT/services/api-mssql"
	[mysql]="$PROJECT_ROOT/services/api-mysql"
	[mongo]="$PROJECT_ROOT/services/api-mongo"
	[neo4j]="$PROJECT_ROOT/services/api-neo4j"
	[supabase]="$PROJECT_ROOT/services/api-supabase"
)

declare -A FRONTEND_PATHS=(
	[mssql]="$PROJECT_ROOT/apps/web-mssql"
	[mysql]="$PROJECT_ROOT/apps/web-mysql"
	[mongo]="$PROJECT_ROOT/apps/web-mongo"
	[neo4j]="$PROJECT_ROOT/apps/web-neo4j"
	[supabase]="$PROJECT_ROOT/apps/web-supabase"
)

declare -A BACKEND_RUNNERS=(
	[mssql]=bun
	[mysql]=bun
	[mongo]=uv
	[neo4j]=uv
	[supabase]=uv
)

declare -A FRONTEND_RUNNERS=(
	[mssql]=bun
	[mysql]=bun
	[mongo]=pnpm
	[neo4j]=pnpm
	[supabase]=pnpm
)

declare -A BACKEND_PORT_DEFAULTS=(
	[mssql]=3000
	[mysql]=3001
	[mongo]=3002
	[neo4j]=3003
	[supabase]=3004
)

declare -A FRONTEND_PORT_DEFAULTS=(
	[mssql]=5000
	[mysql]=5001
	[mongo]=5002
	[neo4j]=5003
	[supabase]=5004
)

log_info() {
	printf '[info] %s\n' "$1"
}

log_warn() {
	printf '[warn] %s\n' "$1"
}

log_error() {
	printf '[err] %s\n' "$1" >&2
}

show_help() {
	cat <<'EOF'
Uso: ./scripts/dev.sh [--up|--down|--init] [stack]

Stacks disponibles:
  mssql, mysql, mongo, all

Acciones:
  --up    Levanta base de datos, backend y frontend en ese orden
  --down  Detiene frontend, backend y baja la base de datos
  --init  Re-crea la base de datos con el perfil init y vuelve a levantar todo

Ejemplos:
  ./scripts/dev.sh --up mssql
  ./scripts/dev.sh --down mysql
  ./scripts/dev.sh --init all
EOF
}

ensure_command() {
	local cmd=$1
	if ! command -v "$cmd" >/dev/null 2>&1; then
		log_error "El comando '$cmd' es requerido"
		exit 1
	fi
}

detect_compose() {
	if docker compose version >/dev/null 2>&1; then
		COMPOSE_CMD=(docker compose)
	elif command -v docker-compose >/dev/null 2>&1; then
		COMPOSE_CMD=(docker-compose)
	else
		log_error "Docker Compose no está disponible"
		exit 1
	fi
}

read_env_value() {
	local file=$1
	local key=$2
	local default=$3
	[[ -f "$file" ]] || { printf '%s' "$default"; return; }
	local line
	line=$(grep -E "^$key=" "$file" | tail -n 1 || true)
	if [[ -z "$line" ]]; then
		printf '%s' "$default"
	else
		local value=${line#*=}
		value=${value%$'\r'}
		value=${value#\"}
		value=${value%\"}
		printf '%s' "$value"
	fi
}

backend_env_file() {
	local stack=$1
	local base=${BACKEND_PATHS[$stack]}
	if [[ -f "$base/.env.local" ]]; then
		printf '%s/.env.local' "$base"
	elif [[ -f "$base/.env" ]]; then
		printf '%s/.env' "$base"
	else
		printf ''
	fi
}

frontend_env_file() {
	local stack=$1
	local base=${FRONTEND_PATHS[$stack]}
	if [[ -f "$base/.env.local" ]]; then
		printf '%s/.env.local' "$base"
	elif [[ -f "$base/.env" ]]; then
		printf '%s/.env' "$base"
	else
		printf ''
	fi
}

resolve_backend_port() {
	local stack=$1
	local env_file
	env_file=$(backend_env_file "$stack")
	read_env_value "$env_file" PORT "${BACKEND_PORT_DEFAULTS[$stack]}"
}

resolve_frontend_port() {
	local stack=$1
	local env_file
	env_file=$(frontend_env_file "$stack")
	read_env_value "$env_file" PORT "${FRONTEND_PORT_DEFAULTS[$stack]}"
}

ensure_network() {
	local network=sales_net
	if ! docker network inspect "$network" >/dev/null 2>&1; then
		log_info "Creando red Docker '$network'"
		docker network create "$network" >/dev/null
	fi
}

sync_uv_dependencies() {
	local stack=$1
	local path=$2
	log_info "Sincronizando dependencias uv para backend $stack"
	(cd "$path" && uv sync)
}

install_bun_dependencies() {
	local role=$1
	local stack=$2
	local path=$3
	if [[ ! -f "$path/package.json" ]]; then
		log_warn "No se encontró package.json para $role $stack, se omite bun install"
		return
	fi
	log_info "Instalando dependencias bun para $role $stack"
	(cd "$path" && bun install)
}

start_database() {
	local stack=$1
	local init_flag=$2
	local compose_file=${DB_COMPOSE_FILES[$stack]:-}

	if [[ -z "$compose_file" ]]; then
		log_info "Stack $stack no tiene base de datos local que levantar"
		return
	fi

	if [[ ! -f "$compose_file" ]]; then
		log_error "No se encontró el compose de $stack en $compose_file"
		exit 1
	fi

	ensure_network

	if [[ "$init_flag" == "true" ]]; then
		log_info "Reinicializando base de datos $stack"
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" down --volumes --remove-orphans >/dev/null 2>&1 || true
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" --profile init up -d
	else
		log_info "Levantando base de datos $stack"
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" up -d
	fi
}

stop_database() {
	local stack=$1
	local compose_file=${DB_COMPOSE_FILES[$stack]:-}
	if [[ -n "$compose_file" && -f "$compose_file" ]]; then
		log_info "Deteniendo base de datos $stack"
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" down --remove-orphans >/dev/null 2>&1 || true
	else
		log_info "Stack $stack no tiene base de datos local que detener"
	fi
}

run_process() {
	local name=$1
	local workdir=$2
	local cmd=$3
	local pid_file="$PID_DIR/$name.pid"
	local log_file="$LOG_DIR/$name.log"

	if [[ -f "$pid_file" ]]; then
		local existing_pid
		existing_pid=$(cat "$pid_file")
		if kill -0 "$existing_pid" >/dev/null 2>&1; then
			log_info "$name ya se está ejecutando (PID $existing_pid)"
			return
		fi
	fi

	: >"$log_file"
	(
		cd "$workdir"
		nohup bash -lc "$cmd" >>"$log_file" 2>&1 &
		echo $! >"$pid_file"
	)
	local pid
	pid=$(cat "$pid_file")
	log_info "$name iniciado (PID $pid)"
}

stop_process() {
	local name=$1
	local pid_file="$PID_DIR/$name.pid"
	if [[ ! -f "$pid_file" ]]; then
		log_warn "No hay PID registrado para $name"
		return
	fi
	local pid
	pid=$(cat "$pid_file")
	if kill -0 "$pid" >/dev/null 2>&1; then
		log_info "Deteniendo $name (PID $pid)"
		kill "$pid" >/dev/null 2>&1 || true
		sleep 1
		if kill -0 "$pid" >/dev/null 2>&1; then
			kill -9 "$pid" >/dev/null 2>&1 || true
		fi
	else
		log_warn "$name no está ejecutándose"
	fi
	rm -f "$pid_file"
}

start_backend() {
	local stack=$1
	local path=${BACKEND_PATHS[$stack]}
	local runner=${BACKEND_RUNNERS[$stack]}
	local port
	port=$(resolve_backend_port "$stack")

	[[ -d "$path" ]] || { log_error "No existe backend para $stack"; exit 1; }

	case "$runner" in
		bun)
			ensure_command bun
			install_bun_dependencies backend "$stack" "$path"
			local cmd="PORT=$port bun run dev"
			run_process "backend-$stack" "$path" "$cmd"
			;;
		pnpm)
			ensure_command pnpm
			local cmd="PORT=$port pnpm run dev"
			run_process "backend-$stack" "$path" "$cmd"
			;;
		uv)
			ensure_command uv
			sync_uv_dependencies "$stack" "$path"
			local cmd="PORT=$port uv run dev"
			run_process "backend-$stack" "$path" "$cmd"
			;;
		*)
			log_error "Runner desconocido para backend $stack"
			exit 1
			;;
	esac
}

start_frontend() {
	local stack=$1
	local path=${FRONTEND_PATHS[$stack]}
	local runner=${FRONTEND_RUNNERS[$stack]}
	local port
	port=$(resolve_frontend_port "$stack")

	[[ -d "$path" ]] || { log_error "No existe frontend para $stack"; exit 1; }

	case "$runner" in
		bun)
			ensure_command bun
			install_bun_dependencies frontend "$stack" "$path"
			local cmd="PORT=$port bun run dev"
			run_process "frontend-$stack" "$path" "$cmd"
			;;
		pnpm)
			ensure_command pnpm
			local cmd="PORT=$port pnpm run dev"
			run_process "frontend-$stack" "$path" "$cmd"
			;;
		*)
			log_error "Runner desconocido para frontend $stack"
			exit 1
			;;
	esac
}

stop_stack_processes() {
	local stack=$1
	stop_process "frontend-$stack"
	stop_process "backend-$stack"
}

run_prisma_tasks() {
	local stack=$1
	local path=${BACKEND_PATHS[$stack]}
	if [[ "$stack" != "mssql" && "$stack" != "mysql" ]]; then
		return
	fi
	ensure_command bun
	if [[ ! -f "$path/package.json" ]]; then
		log_warn "No hay package.json en $path para ejecutar Prisma"
		return
	fi
	log_info "Ejecutando Prisma generate para $stack"
	(cd "$path" && bun run db:generate)
	if grep -q '"db:push"' "$path/package.json"; then
		log_info "Ejecutando Prisma db:push para $stack"
		(cd "$path" && bun run db:push)
	fi
}

summary_urls() {
	local stack=$1
	local backend_port
	backend_port=$(resolve_backend_port "$stack")
	local frontend_port
	frontend_port=$(resolve_frontend_port "$stack")
	log_info "Backend $stack: http://localhost:$backend_port"
	log_info "Frontend $stack: http://localhost:$frontend_port"
	log_info "Logs backend: $LOG_DIR/backend-$stack.log"
	log_info "Logs frontend: $LOG_DIR/frontend-$stack.log"
}

handle_up() {
	local stack=$1
	start_database "$stack" false
	start_backend "$stack"
	start_frontend "$stack"
	summary_urls "$stack"
}

handle_init() {
	local stack=$1
	stop_stack_processes "$stack"
	start_database "$stack" true
	run_prisma_tasks "$stack"
	start_backend "$stack"
	start_frontend "$stack"
	summary_urls "$stack"
}

handle_down() {
	local stack=$1
	stop_stack_processes "$stack"
	stop_database "$stack"
}

parse_args() {
	ACTION=""
	TARGETS=()
	local include_all=false

	while [[ $# -gt 0 ]]; do
		case "$1" in
			--up|--down|--init)
				if [[ -n "$ACTION" ]]; then
					log_error "Solo se permite una acción por ejecución"
					exit 1
				fi
				ACTION=${1#--}
				shift
				;;
			all)
				include_all=true
				shift
				;;
			mssql|mysql|mongo|neo4j|supabase)
				TARGETS+=("$1")
				shift
				;;
			--help|-h)
				show_help
				exit 0
				;;
			*)
				log_error "Argumento no reconocido: $1"
				show_help
				exit 1
				;;
		esac
	done

	if [[ -z "$ACTION" ]]; then
		log_error "Debes especificar --up, --down o --init"
		exit 1
	fi

	if [[ "$include_all" == true ]]; then
		TARGETS=(${STACKS[@]})
	elif [[ ${#TARGETS[@]} -eq 0 ]]; then
		TARGETS=(${STACKS[@]})
	fi
}

main() {
	ensure_command docker
	ensure_command grep
	ensure_command bash
	detect_compose
	parse_args "$@"

	for stack in "${TARGETS[@]}"; do
		case "$stack" in
			mssql|mysql|mongo|neo4j|supabase) ;;
			*)
				log_error "Stack desconocido: $stack"
				exit 1
				;;
		esac
		case "$ACTION" in
			up)
				handle_up "$stack"
				;;
			down)
				handle_down "$stack"
				;;
			init)
				handle_init "$stack"
				;;
		esac
	done
}

main "$@"
