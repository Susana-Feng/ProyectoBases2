
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
	echo "[err] No .env.local or .env found in project root" >&2
	exit 1
fi

STACKS=(mssql mysql mongo neo4j supabase)

MSSQL_MODE="remote"
MSSQL_REMOTE_COMPOSE="$INFRA_DB_DIR/mssql/compose.yaml"
MSSQL_LOCAL_COMPOSE="$INFRA_DB_DIR/mssql/compose.localdb.yaml"
MSSQL_INIT_CONTAINER_REMOTE="mssql_sales_init"
MSSQL_INIT_CONTAINER_LOCAL="mssql_sales_init_local"
SUPABASE_COMPOSE="$INFRA_DB_DIR/supabase/compose.yaml"
SUPABASE_INIT_CONTAINER="supabase_sales_init"

declare -A DB_COMPOSE_FILES=(
	[mssql]="$MSSQL_REMOTE_COMPOSE"
	[mysql]="$INFRA_DB_DIR/mysql/compose.yaml"
	[mongo]="$INFRA_DB_DIR/mongo/compose.yaml"
	[neo4j]="$INFRA_DB_DIR/neo4j/compose.yaml"
	[supabase]="$SUPABASE_COMPOSE"
)

declare -A BACKEND_PATHS=(
	[mssql]="$PROJECT_ROOT/services/api-mssql"
	[mysql]="$PROJECT_ROOT/services/api-mysql"
	[mongo]="$PROJECT_ROOT/services/api-mongo"
	[neo4j]="$PROJECT_ROOT/services/api-neo4j"
	[supabase]="$PROJECT_ROOT/services/api-supabase"
)

declare -A BACKEND_RUNNERS=(
	[mssql]="bun"
	[mysql]="bun"
	[mongo]="uv"
	[neo4j]="uv"
	[supabase]="uv"
)

declare -A BACKEND_PORT_DEFAULTS=(
	[mssql]=3000
	[mysql]=3001
	[mongo]=3002
	[neo4j]=3003
	[supabase]=3004
)

declare -A FRONTEND_PATHS=(
	[mssql]="$PROJECT_ROOT/apps/web-mssql"
	[mysql]="$PROJECT_ROOT/apps/web-mysql"
	[mongo]="$PROJECT_ROOT/apps/web-mongo"
	[neo4j]="$PROJECT_ROOT/apps/web-neo4j"
	[supabase]="$PROJECT_ROOT/apps/web-supabase"
)

declare -A FRONTEND_RUNNERS=(
	[mssql]="bun"
	[mysql]="bun"
	[mongo]="pnpm"
	[neo4j]="pnpm"
	[supabase]="pnpm"
)

declare -A FRONTEND_PORT_DEFAULTS=(
	[mssql]=5000
	[mysql]=5001
	[mongo]=5002
	[neo4j]=5003
	[supabase]=5004
)

declare -A INIT_MAX_WAIT=(
	[mssql]=300
	[mysql]=300
	[mongo]=300
	[neo4j]=300
	[supabase]=0
)

OPEN_INDEX_AFTER=false
MSSQL_MODE_EXPLICIT=false

log_warn() {
	printf '[warn] %s\n' "$1"
}

log_error() {
	printf '[err] %s\n' "$1" >&2
}

log_info() {
	printf '[info] %s\n' "$1"
}

open_index_html() {
	local index_file="$PROJECT_ROOT/index.html"
	if [[ ! -f "$index_file" ]]; then
		log_warn "index.html not found in $PROJECT_ROOT"
		return
	fi
	if command -v xdg-open >/dev/null 2>&1; then
		xdg-open "$index_file" >/dev/null 2>&1 &
	elif command -v open >/dev/null 2>&1; then
		open "$index_file" >/dev/null 2>&1 &
	else
		log_warn "No browser command found (xdg-open/open)"
	fi
}

show_help() {
	cat <<'EOF'
Usage: ./scripts/dev.sh [--up|--down|--init] [stack1,stack2,...]
	[--local|--remote]

Available stacks:
  mssql, mysql, mongo, neo4j, supabase, all

Actions:
  --up    Start database, backend and frontend in order
  --down  Stop frontend, backend and database
  --init  Recreate database with init profile and restart everything

Examples:
  ./scripts/dev.sh --up mssql
  ./scripts/dev.sh --down mysql
  ./scripts/dev.sh --init all
  ./scripts/dev.sh --init mssql,mysql
  ./scripts/dev.sh --down mssql,mysql,mongo

MSSQL modes:
  --remote (default)  Use external instance configured in .env*
  --local             Start local SQL Server container and skip BCCR jobs
EOF
}

set_mssql_compose_file() {
	if [[ "$MSSQL_MODE" == "local" ]]; then
		DB_COMPOSE_FILES[mssql]="$MSSQL_LOCAL_COMPOSE"
	else
		DB_COMPOSE_FILES[mssql]="$MSSQL_REMOTE_COMPOSE"
	fi
}

ensure_command() {
	local cmd=$1
	if ! command -v "$cmd" >/dev/null 2>&1; then
		log_error "Command '$cmd' is required"
		exit 1
	fi
}

detect_compose() {
	if docker compose version >/dev/null 2>&1; then
		COMPOSE_CMD=(docker compose)
	elif command -v docker-compose >/dev/null 2>&1; then
		COMPOSE_CMD=(docker-compose)
	else
		log_error "Docker Compose is not available"
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

is_remote_mssql() {
	local host
	host=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_REMOTE_HOST "")
	if [[ -n "$host" ]]; then
		printf 'true'
	else
		printf 'false'
	fi
}

run_remote_mssql_init() {
	local host port pass seed_file sqlcmd_bin server
	host=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_REMOTE_HOST "")
	port=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_REMOTE_PORT "15433")
	pass=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_REMOTE_PASS "YourStrong@Passw0rd1")
	if [[ -z "$host" ]]; then
		log_error "MSSQL_REMOTE_HOST is not defined in $COMPOSE_ENV_FILE"
		exit 1
	fi
	ensure_command sqlcmd
	server="$host,$port"
	log_info "Initializing remote MSSQL at $server"
	for f in $(ls -1 "$INFRA_DB_DIR/mssql/init"/*.sql 2>/dev/null | sort); do
		log_info "Running $(basename "$f") on remote instance"
		sqlcmd -C -S "$server" -U sa -P "$pass" -i "$f"
	done
	seed_file="$PROJECT_ROOT/data/out/mssql_data.sql"
	if [[ -f "$seed_file" ]]; then
		log_info "Running seed $(basename "$seed_file")"
		sqlcmd -C -S "$server" -U sa -P "$pass" -i "$seed_file"
	else
		log_info "Seed mssql_data.sql not found, skipping"
	fi
}

configure_mssql_backend_env() {
	local env_file
	env_file=$(backend_env_file mssql)
	if [[ -z "$env_file" ]]; then
		log_warn "No .env file found for mssql backend"
		return
	fi

	local host port pass mode_label user db
	user=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_USER "sa")
	db=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_SALES_DB "DB_SALES")

	if [[ "$MSSQL_MODE" == "local" ]]; then
		host=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_LOCAL_HOST "localhost")
		port=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_LOCAL_PORT "1433")
		pass=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_LOCAL_PASS "YourStrong@Passw0rd1")
		mode_label="local"
	else
		host=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_REMOTE_HOST "")
		port=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_REMOTE_PORT "15433")
		pass=$(read_env_value "$COMPOSE_ENV_FILE" MSSQL_REMOTE_PASS "YourStrong@Passw0rd1")
		mode_label="remote"
	fi

	if [[ -z "$host" ]]; then
		log_error "No host configured for MSSQL ($MSSQL_MODE) in $COMPOSE_ENV_FILE"
		exit 1
	fi

	local url
	url="sqlserver://$host:$port;database=$db;user=$user;password=$pass;encrypt=true;trustServerCertificate=true"

	if grep -q '^DATABASE_URL=' "$env_file"; then
		sed -i "s|^DATABASE_URL=.*$|DATABASE_URL=\"$url\"|" "$env_file"
	else
		printf 'DATABASE_URL="%s"\n' "$url" >> "$env_file"
	fi
}

maybe_configure_backend_env() {
	local stack=$1
	case "$stack" in
		mssql)
			configure_mssql_backend_env
			;;
		*) ;;
	esac
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
		docker network create "$network" >/dev/null
	fi
}

sync_uv_dependencies() {
	local stack=$1
	local path=$2
	(cd "$path" && uv sync >/dev/null 2>&1)
}

install_bun_dependencies() {
	local role=$1
	local stack=$2
	local path=$3
	if [[ ! -f "$path/package.json" ]]; then
		log_warn "No package.json found for $role $stack, skipping bun install"
		return
	fi
	(cd "$path" && bun install >/dev/null 2>&1)
}

install_pnpm_dependencies() {
	local role=$1
	local stack=$2
	local path=$3
	if [[ ! -f "$path/package.json" ]]; then
		log_warn "No package.json found for $role $stack, skipping pnpm install"
		return
	fi
	(cd "$path" && pnpm install >/dev/null 2>&1)
}

start_database() {
	local stack=$1
	local init_flag=$2
	local compose_file=${DB_COMPOSE_FILES[$stack]:-}

	if [[ "$stack" == "mssql" ]]; then
		if [[ "$MSSQL_MODE" == "remote" && "$init_flag" != "true" ]]; then
			return
		fi
	fi

	if [[ "$stack" == "supabase" && "$init_flag" != "true" ]]; then
		return
	fi

	if [[ -z "$compose_file" ]]; then
		return
	fi

	if [[ ! -f "$compose_file" ]]; then
		log_error "Compose file for $stack not found at $compose_file"
		exit 1
	fi

	ensure_network

	if [[ "$init_flag" == "true" ]]; then
		log_info "Reinitializing database $stack"
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" down --volumes --remove-orphans >/dev/null 2>&1 || true
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" --profile init up -d >/dev/null 2>&1
	else
		log_info "Starting database $stack"
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" up -d >/dev/null 2>&1
	fi
}

wait_for_init_container() {
	local stack=$1
	local container_name=""
	
	case "$stack" in
		mssql)
			if [[ "$MSSQL_MODE" == "local" ]]; then
				container_name="$MSSQL_INIT_CONTAINER_LOCAL"
			else
				container_name="$MSSQL_INIT_CONTAINER_REMOTE"
			fi
			;;
		mysql) container_name="mysql_sales_init" ;;
		mongo) container_name="mongo_sales_init" ;;
		neo4j) container_name="neo4j_sales_init" ;;
		supabase) container_name="$SUPABASE_INIT_CONTAINER" ;;
		*) return ;;
	esac
	
	# Check if container exists
	if ! docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
		return
	fi
	
	local max_wait=${INIT_MAX_WAIT[$stack]:-300}
	local unlimited=false
	if [[ "$max_wait" -le 0 ]]; then
		unlimited=true
	fi
	local waited=0
	local interval=5
	
	printf '[info] Waiting for %s initialization... (0s)' "$stack"
	
	while true; do
		local status
		status=$(docker inspect -f '{{.State.Status}}' "$container_name" 2>/dev/null || echo "not_found")
		
		case "$status" in
			"exited")
				local exit_code
				exit_code=$(docker inspect -f '{{.State.ExitCode}}' "$container_name" 2>/dev/null || echo "1")
				if [[ "$exit_code" == "0" ]]; then
					printf '\r[info] Waiting for %s initialization... done                    \n' "$stack"
					return 0
				else
					printf '\r[info] Waiting for %s initialization... failed (exit code: %s)\n' "$stack" "$exit_code"
					log_error "Check logs with: docker logs $container_name"
					return 1
				fi
				;;
			"running")
				sleep $interval
				waited=$((waited + interval))
				printf '\r[info] Waiting for %s initialization... (%ds)' "$stack" "$waited"
				;;
			"not_found")
				printf '\r[info] Waiting for %s initialization... done                    \n' "$stack"
				return 0
				;;
			*)
				sleep $interval
				waited=$((waited + interval))
				printf '\r[info] Waiting for %s initialization... (%ds)' "$stack" "$waited"
				;;
		esac

			if [[ "$unlimited" != true && $waited -ge $max_wait ]]; then
				printf '\r[info] Waiting for %s initialization... timeout (%ds)\n' "$stack" "$max_wait"
				log_error "Check logs with: docker logs $container_name"
				return 1
			fi
	done
}

stop_database() {
	local stack=$1
	local compose_file=${DB_COMPOSE_FILES[$stack]:-}
	if [[ -n "$compose_file" && -f "$compose_file" ]]; then
		log_info "Stopping database $stack"
		"${COMPOSE_CMD[@]}" -f "$compose_file" --env-file "$COMPOSE_ENV_FILE" down --remove-orphans >/dev/null 2>&1 || true
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
			log_info "$name already running (PID $existing_pid)"
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
	log_info "$name started (PID $pid)"
}

stop_process() {
	local name=$1
	local pid_file="$PID_DIR/$name.pid"
	if [[ ! -f "$pid_file" ]]; then
		return
	fi
	local pid
	pid=$(cat "$pid_file")
	if kill -0 "$pid" >/dev/null 2>&1; then
		log_info "Stopping $name (PID $pid)"
		kill "$pid" >/dev/null 2>&1 || true
		sleep 1
		if kill -0 "$pid" >/dev/null 2>&1; then
			kill -9 "$pid" >/dev/null 2>&1 || true
		fi
	fi
	rm -f "$pid_file"
}

start_backend() {
	local stack=$1
	local path=${BACKEND_PATHS[$stack]}
	local runner=${BACKEND_RUNNERS[$stack]}
	local port
	port=$(resolve_backend_port "$stack")

	[[ -d "$path" ]] || { log_error "Backend for $stack does not exist"; exit 1; }

	maybe_configure_backend_env "$stack"

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
			log_error "Unknown runner for backend $stack"
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

	[[ -d "$path" ]] || { log_error "Frontend for $stack does not exist"; exit 1; }

	case "$runner" in
		bun)
			ensure_command bun
			install_bun_dependencies frontend "$stack" "$path"
			local cmd="PORT=$port bun run dev"
			run_process "frontend-$stack" "$path" "$cmd"
			;;
		pnpm)
			ensure_command pnpm
			install_pnpm_dependencies frontend "$stack" "$path"
			local cmd="PORT=$port pnpm run dev"
			run_process "frontend-$stack" "$path" "$cmd"
			;;
		*)
			log_error "Unknown runner for frontend $stack"
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
	maybe_configure_backend_env "$stack"
	ensure_command bun
	if [[ ! -f "$path/package.json" ]]; then
		log_warn "No package.json in $path to run Prisma"
		return
	fi
	# Install dependencies before running Prisma
	install_bun_dependencies backend "$stack" "$path"
	(cd "$path" && bun run db:generate >/dev/null 2>&1)
	if grep -q '"db:push"' "$path/package.json"; then
		(cd "$path" && bun run db:push >/dev/null 2>&1)
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
	wait_for_init_container "$stack"
	if [[ "$stack" == "mssql" || "$stack" == "mysql" ]]; then
		run_prisma_tasks "$stack"
	fi
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
	local mode_override=""

	while [[ $# -gt 0 ]]; do
		case "$1" in
			--up|--down|--init)
				if [[ -n "$ACTION" ]]; then
					log_error "Only one action allowed per execution"
					exit 1
				fi
				ACTION=${1#--}
				shift
				;;
			--local)
				mode_override="local"
				MSSQL_MODE_EXPLICIT=true
				shift
				;;
			--remote)
				mode_override="remote"
				MSSQL_MODE_EXPLICIT=true
				shift
				;;
			all)
				include_all=true
				shift
				;;
			--help|-h)
				show_help
				exit 0
				;;
			*)
				# Handle comma-separated stacks (e.g. mssql,mysql,mongo)
				IFS=',' read -ra STACK_LIST <<< "$1"
				local valid_stack=false
				for stack_item in "${STACK_LIST[@]}"; do
					case "$stack_item" in
						mssql|mysql|mongo|neo4j|supabase)
							TARGETS+=("$stack_item")
							valid_stack=true
							;;
						*)
							log_error "Unrecognized argument: $stack_item"
							show_help
							exit 1
							;;
					esac
				done
				shift
				;;
		esac
	done

	if [[ -z "$ACTION" ]]; then
		log_error "You must specify --up, --down or --init"
		exit 1
	fi

	if [[ -n "$mode_override" ]]; then
		MSSQL_MODE="$mode_override"
	fi

	if [[ "$ACTION" == "init" && "$MSSQL_MODE_EXPLICIT" == false ]]; then
		MSSQL_MODE="remote"
	fi

	if [[ "$include_all" == true ]]; then
		TARGETS=(${STACKS[@]})
		if [[ "$ACTION" != "down" ]]; then
			OPEN_INDEX_AFTER=true
		fi
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
	set_mssql_compose_file

	for stack in "${TARGETS[@]}"; do
		case "$stack" in
			mssql|mysql|mongo|neo4j|supabase) ;;
			*)
				log_error "Unknown stack: $stack"
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

	if [[ "$OPEN_INDEX_AFTER" == true && "$ACTION" != "down" ]]; then
		open_index_html
	fi
}

main "$@"
