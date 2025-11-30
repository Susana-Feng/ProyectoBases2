#!/usr/bin/env bash
set -euo pipefail

HOST="${SUPABASE_DB_HOST:-}"
PORT="${SUPABASE_DB_PORT:-5432}"
USER="${SUPABASE_DB_USER:-postgres}"
DB="${SUPABASE_DB_NAME:-postgres}"
PASS="${SUPABASE_DB_PASS:-}"

if [[ -z "$HOST" || -z "$PASS" ]]; then
  echo "[err] Debes definir SUPABASE_DB_HOST y SUPABASE_DB_PASS" >&2
  exit 1
fi

export PGPASSWORD="$PASS"
export PGSSLMODE="${PGSSLMODE:-require}"

# Scripts are mounted in /scripts, data files in /workspace
SCRIPT_DIR="/scripts"
DATA_FILE="/workspace/data/out/supabase_data.sql"

echo "[info] Ejecutando scripts contra Supabase ($HOST:$PORT/$DB)"

# Execute schema
echo "[info] Aplicando schema..."
psql \
  --host "$HOST" \
  --port "$PORT" \
  --username "$USER" \
  --dbname "$DB" \
  --set ON_ERROR_STOP=1 \
  --file "$SCRIPT_DIR/00_schema.sql"

# Execute data load
if [[ -f "$DATA_FILE" ]]; then
  echo "[info] Cargando datos desde $DATA_FILE..."
  psql \
    --host "$HOST" \
    --port "$PORT" \
    --username "$USER" \
    --dbname "$DB" \
    --set ON_ERROR_STOP=1 \
    --file "$DATA_FILE"
else
  echo "[warn] No se encontró $DATA_FILE, omitiendo carga de datos"
fi

echo "[info] Supabase init completado"
