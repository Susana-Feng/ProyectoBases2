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

# Ejecutar todos los .sql en orden alfabético (00_*, 10_*, 20_*, 30_* ...)
for f in $(ls -1 /scripts/*.sql 2>/dev/null | sort); do
  run_sql "$f"
done

SEED_FILE="/seed_data/mssql_data.sql"
if [ -f "$SEED_FILE" ]; then
  echo ">> Ejecutando seed $(basename "$SEED_FILE")"
  run_sql "$SEED_FILE"
else
  echo ">> Seed mssql_data.sql no encontrado, se omite"
fi

echo ">> init_sales OK"
