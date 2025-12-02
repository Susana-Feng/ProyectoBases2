#!/usr/bin/env bash
set -euo pipefail

HOST="${MSSQL_HOST:-mssql_sales}"
PORT="${MSSQL_PORT:-1433}"
PASS="${MSSQL_SA_PASSWORD:-YourStrong@Passw0rd1}"
SKIP_BCCR_JOBS="${SKIP_BCCR_JOBS:-false}"

# BCCR credentials from environment
BCCR_TOKEN="${BCCR_TOKEN:-}"
BCCR_EMAIL="${BCCR_EMAIL:-}"
BCCR_NOMBRE="${BCCR_NOMBRE:-}"

SQLCMD="/opt/mssql-tools18/bin/sqlcmd"
if [ ! -x "$SQLCMD" ]; then
  SQLCMD="/opt/mssql-tools/bin/sqlcmd"
fi
# último fallback: que esté en el PATH
if [ ! -x "$SQLCMD" ]; then
  SQLCMD="sqlcmd"
fi

run_sql() {
  local f="$1"
  echo ">> Ejecutando $(basename "$f")"
  "$SQLCMD" -b -C -S "$HOST,$PORT" -U sa -P "$PASS" -i "$f"
}

preprocess_bccr_sql() {
  # Preprocess BCCR SQL file to replace placeholders with env values
  local bccr_file="$1"
  local temp_file="/tmp/40_bccr_jobs_processed.sql"
  
  if [[ -z "$BCCR_TOKEN" || -z "$BCCR_EMAIL" || -z "$BCCR_NOMBRE" ]]; then
    echo ">> WARNING: BCCR credentials not set in environment"
    echo ">> BCCR job will use placeholder values (won't work for real data)"
    return 1
  fi
  
  echo ">> Injecting BCCR credentials into SQL script"
  cp "$bccr_file" "$temp_file"
  sed -i "s|__BCCR_TOKEN__|${BCCR_TOKEN}|g" "$temp_file"
  sed -i "s|__BCCR_EMAIL__|${BCCR_EMAIL}|g" "$temp_file"
  sed -i "s|__BCCR_NOMBRE__|${BCCR_NOMBRE}|g" "$temp_file"
  
  echo "$temp_file"
}

# Ejecutar todos los .sql en orden alfabético (00_*, 10_*, 20_*, 30_* ...)
for f in $(ls -1 /scripts/*.sql 2>/dev/null | sort); do
  base_name="$(basename "$f")"
  
  if [[ "$SKIP_BCCR_JOBS" == "true" && "$base_name" == "40_bccr_jobs.sql" ]]; then
    echo ">> Omitiendo $base_name (jobs deshabilitados)"
    continue
  fi
  
  # Special handling for BCCR jobs file - preprocess to inject credentials
  if [[ "$base_name" == "40_bccr_jobs.sql" ]]; then
    processed_file=$(preprocess_bccr_sql "$f" || echo "")
    if [[ -n "$processed_file" && -f "$processed_file" ]]; then
      run_sql "$processed_file"
      rm -f "$processed_file"
    else
      run_sql "$f"
    fi
  else
    run_sql "$f"
  fi
done

SEED_FILE="/seed_data/mssql_data.sql"
if [ -f "$SEED_FILE" ]; then
  echo ">> Ejecutando seed $(basename "$SEED_FILE")"
  run_sql "$SEED_FILE"
else
  echo ">> Seed mssql_data.sql no encontrado, se omite"
fi

echo ">> init_sales OK"
