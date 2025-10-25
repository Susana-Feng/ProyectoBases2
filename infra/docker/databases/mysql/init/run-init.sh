#!/usr/bin/env bash
set -euo pipefail

HOST="${MYSQL_HOST:-mysql_sales}"
PASS="${MYSQL_ROOT_PASSWORD:-YourStrong@Passw0rd1}"

run_sql() {
  local f="$1"
  local db="${2:-}"
  echo ">> Ejecutando $(basename "$f")"
  if [ -z "$db" ]; then
    mysql -h "$HOST" -u root -p"$PASS" < "$f"
  else
    mysql -h "$HOST" -u root -p"$PASS" "$db" < "$f"
  fi
}

[ -f /scripts/00_create_db.sql ] && run_sql /scripts/00_create_db.sql
[ -f /scripts/10_schema.sql ] && run_sql /scripts/10_schema.sql DB_SALES
[ -f /scripts/20_seed_data.sql ] && run_sql /scripts/20_seed_data.sql DB_SALES

echo ">> init_sales OK"
