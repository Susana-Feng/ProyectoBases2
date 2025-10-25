#!/usr/bin/env bash
set -euo pipefail

HOST="${MSSQL_HOST:-mssql_sales}"
PASS="${MSSQL_SA_PASSWORD:-YourStrong@Passw0rd1}"

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
  "$SQLCMD" -b -C -S "$HOST" -U sa -P "$PASS" -i "$f"
}

[ -f /scripts/00_create_db.sql ] && run_sql /scripts/00_create_db.sql
[ -f /scripts/10_schema.sql ] && run_sql /scripts/10_schema.sql
echo ">> init_sales OK"
