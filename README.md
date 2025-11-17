# ProyectoBases2

**Instituto Tecnológico de Costa Rica**  
Campus Tecnológico Central Cartago  
Escuela de Ingeniería en Computación  

**Curso**: IC4302 Bases de datos II  
**Profesor**: Diego Andres Mora Rojas  
**Semestre**: II Semestre, 2025  

## Integrantes

- <REMOVED_BCCR_NAME>
- Susana Feng Liu
- Ximena Molina Portilla
- Aarón Vásquez Báñez

## Estructura propuesta para el repositorio

```text
ProyectoBases2/
├── etl/                 # Etl & Job en Python
├── infra/               # Configuración Docker
├── services/            # APIs (FastAPI/Express)
├── apps/                # Frontends React
├── docs/                # Documentación
└── scripts/             # Scripts de utilidad
```

## Inicio rápido

### 1. Preparar entorno

#### Crear red compartida

```bash
# Crear la red bridge compartida para todas las bases de datos (si no existe)
docker network create --driver bridge sales_net || echo "La red sales_net ya existe"
```

#### Variables de entorno

Crea un archivo `.env.local` basado en `.env.example`:

```bash
# MSSQL - Sales y Datawarehouse
MSSQL_SA_PASS=YourStrong@Passw0rd1
MSSQL_SA_PORT=1433

# MySQL
MYSQL_ROOT_PASS=YourStrong@Passw0rd1
MYSQL_USER=sales_user
MYSQL_PASS=sales_pass_123
MYSQL_PORT=3306

# Neo4j
NEO4J_AUTH=neo4j/ChangeMe123!
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
```

### 2. Levantar bases de datos

#### Linux/macOS

Usa el script `dev_up.sh` para gestionar las bases de datos de desarrollo:

```bash
# Levantar todas las bases de datos disponibles
./scripts/dev_up.sh

# Levantar todas las bases de datos (explícito)
./scripts/dev_up.sh --up all

# Levantar solo MSSQL
./scripts/dev_up.sh --up mssql

# Reinicializar MSSQL (borra datos existentes y vuelve a crear)
./scripts/dev_up.sh --init mssql

# Reinicializar MySQL
./scripts/dev_up.sh --init mysql

# Reinicializar todas las bases de datos
./scripts/dev_up.sh --init all

# Detener todas las bases de datos
./scripts/dev_up.sh --down all

# Ver logs de MySQL
./scripts/dev_up.sh --logs mysql

# Ver ayuda completa
./scripts/dev_up.sh --help
```

#### Windows (PowerShell)

Usa el script `dev_up.ps1` para gestionar las bases de datos de desarrollo:

```powershell
# Levantar todas las bases de datos disponibles
.\scripts\dev_up.ps1

# Levantar todas las bases de datos (explícito)
.\scripts\dev_up.ps1 -Up all

# Levantar solo MSSQL
.\scripts\dev_up.ps1 -Up mssql

# Reinicializar MSSQL (borra datos existentes y vuelve a crear)
.\scripts\dev_up.ps1 -Init mssql

# Reinicializar MySQL
.\scripts\dev_up.ps1 -Init mysql

# Reinicializar todas las bases de datos
.\scripts\dev_up.ps1 -Init all

# Detener todas las bases de datos
.\scripts\dev_up.ps1 -Down all

# Ver logs de MySQL
.\scripts\dev_up.ps1 -Logs mysql

# Ver ayuda completa
.\scripts\dev_up.ps1 -Help
```

**Nota para Windows**: Si es la primera vez que ejecutas scripts PowerShell, abre PowerShell como administrador y ejecuta:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Bases de datos disponibles

- **MSSQL**: Microsoft SQL Server 2022 con base de datos `DB_SALES` y esquema `sales_ms`
- **MySQL**: MySQL 8.x con base de datos `DB_SALES`
- **Neo4j**: Neo4j con base de datos `db-sales`
- **MongoDB**: MongoDB Atlas (externo)
- **PostgreSQL**: Supabase (externo)

## Desarrollo

```bash
# 1. Levantar la BD
docker compose -f infra/docker/databases/mssql/compose.yaml \
  --env-file .env.local \
  up -d mssql_sales

# 2. Inicializar BD
docker compose -f infra/docker/databases/mssql/compose.yaml \
  --env-file .env.local \
  --profile init \
  up init_sales

# 3. Ver logs de inicialización
docker compose -f infra/docker/databases/mssql/compose.yaml \
  --env-file .env.local \
  logs -f init_sales

# 3. Ver logs de la BD
docker compose -f infra/docker/databases/mssql/compose.yaml \
  --env-file .env.local \
  logs -f mssql_sales

# 4. Parar servicios
docker compose -f infra/docker/databases/mssql/compose.yaml \
  --env-file .env.local \
  down --volumes --remove-orphans
```
