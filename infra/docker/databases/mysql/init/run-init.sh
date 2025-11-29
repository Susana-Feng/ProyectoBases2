#!/usr/bin/env bash
set -euo pipefail

HOST="${MYSQL_HOST:-mysql_sales}"
PASS="${MYSQL_ROOT_PASSWORD:-YourStrong@Passw0rd1}"

run_sql() {
  local f="$1"
  local db="${2:-}"
  echo ">> Ejecutando $(basename "$f")"
  if [ -z "$db" ]; then
    mysql --default-character-set=utf8mb4 -h "$HOST" -u root -p"$PASS" < "$f"
  else
    mysql --default-character-set=utf8mb4 -h "$HOST" -u root -p"$PASS" "$db" < "$f"
  fi
}

# Ejecutar 00_database.sql sin contexto de DB
[ -f /scripts/00_database.sql ] && run_sql /scripts/00_database.sql

# Ejecutar todos los demás .sql en orden alfabético contra DB_SALES
for f in $(ls -1 /scripts/*.sql 2>/dev/null | grep -v "00_database" | sort); do
  run_sql "$f" DB_SALES
done

SEED_FILE="/seed_data/mysql_data.sql"
if [ -f "$SEED_FILE" ]; then
  echo ">> Ejecutando seed $(basename "$SEED_FILE")"
  run_sql "$SEED_FILE" DB_SALES
else
  echo ">> Seed mysql_data.sql no encontrado, se omite"
fi

echo ">> init_sales OK"
