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
INIT_FILE="/workspace/scripts/Supabase/init.sql"

if [[ ! -f "$INIT_FILE" ]]; then
  echo "[err] No se encontró $INIT_FILE" >&2
  exit 1
fi

echo "[info] Ejecutando init.sql contra Supabase ($HOST:$PORT/$DB)"
psql \
  --host "$HOST" \
  --port "$PORT" \
  --username "$USER" \
  --dbname "$DB" \
  --set ON_ERROR_STOP=1 \
  --file "$INIT_FILE"

echo "[info] Supabase init completado"
