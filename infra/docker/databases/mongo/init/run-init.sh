#!/usr/bin/env bash
set -euo pipefail

MONGO_HOST="${MONGO_HOST:-mongo_sales}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_DB="${MONGO_DB:-tiendaDB}"
# Usar las variables del compose (MONGO_INITDB_ROOT_*) o las del .env.local (MONGO_USER/MONGO_PASS)
MONGO_ROOT_USER="${MONGO_INITDB_ROOT_USERNAME:-${MONGO_USER:-root}}"
MONGO_ROOT_PASS="${MONGO_INITDB_ROOT_PASSWORD:-${MONGO_PASS:-YourStrong@Passw0rd1}}"

# Esperar a que Mongo esté accesible
until mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASS" --authenticationDatabase admin --eval "db.adminCommand('ping')" >/dev/null 2>&1; do
  echo "Esperando a que MongoDB esté listo en $MONGO_HOST:$MONGO_PORT..."
  sleep 3
done

echo "MongoDB listo. Ejecutando scripts de inicialización..."

# Ejecutar scripts .js de inicialización en orden
for script in /scripts/*.js; do
  if [ -f "$script" ]; then
    echo "Ejecutando $script"
    mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASS" --authenticationDatabase admin "$MONGO_DB" "$script"
  fi
done

SEED_JS="/seed_data/mongo_data.js"
if [ -f "$SEED_JS" ]; then
  echo "Ejecutando seed $SEED_JS"
  mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASS" --authenticationDatabase admin "$MONGO_DB" "$SEED_JS"
else
  echo "Seed mongo_data.js no encontrado, se omite"
fi

echo "Inicialización de MongoDB completada."
