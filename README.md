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
bd2-proyecto/
├─ .github/
│  └─ workflows/
│     ├─ ci-node.yml                 # Lint, build y tests para Node/React/TypeScript
│     ├─ ci-python.yml               # Lint (ruff), tests (pytest), notebooks
│     └─ release.yml                 # Versionado y build de imágenes (opcional)
├─ docs/
│  ├─ arquitectura.md                # Visión general, diagramas y decisiones
│  ├─ diccionario-datos.md           # Campos, dominios, llaves, convenciones
│  ├─ etl-reglas.md                  # Reglas de negocio y transformación (moneda, fechas, etc.)
│  └─ powerbi-kpis-y-graficos.md     # KPIs, medidas DAX, filtros y layout de reportes
├─ infra/
│  └─ docker/
│     ├─ compose.dev.yml             # Orquestador para levantar stacks de desarrollo por perfiles
│     └─ databases/
│        ├─ mssql/
│        │  ├─ compose.yml           # SQL Server Developer con healthcheck
│        │  ├─ init/                 # Scripts aplicados con sqlcmd tras estar healthy
│        │  │  ├─ 00_create_db.sql
│        │  │  ├─ 10_schema_dw.sql   # Dimensiones, hechos, índices
│        │  │  └─ 20_seed.sql
│        │  └─ scripts/
│        │     ├─ wait-for-mssql.sh
│        │     └─ init.sh
│        ├─ mysql/
│        │  ├─ compose.yml           # MySQL 8.x con /docker-entrypoint-initdb.d
│        │  ├─ conf/                 # my.cnf opcional
│        │  └─ initdb/
│        │     ├─ 00_create_db.sql
│        │     ├─ 10_schema.sql
│        │     └─ 20_seed.sql
│        ├─ mongo/
│        │  ├─ compose.yml           # MongoDB + mongo-express (opcional)
│        │  ├─ dumps/                # Backups para mongorestore (opcional)
│        │  └─ initdb/               # JS/SH ejecutados al arranque
│        │     ├─ 00_create_user.js
│        │     └─ 10_seed.js
│        └─ neo4j/
│           ├─ compose.yml           # Neo4j con plugins (APOC/GDS si aplica)
│           ├─ conf/                 # neo4j.conf
│           ├─ plugins/              # JARs opcionales
│           ├─ import/               # CSV para LOAD CSV
│           └─ init/                 # Cypher aplicados con cypher-shell
│              ├─ 00_constraints.cypher
│              └─ 10_seed.cypher
├─ data/
│  ├─ raw/                           # Archivos de origen sin procesar (CSV, JSON, dumps)
│  ├─ staging/                       # Datos intermedios del ETL (CSV/Parquet)
│  └─ samples/                       # Subconjuntos pequeños para pruebas
├─ dw/
│  ├─ mssql/
│  │  ├─ 001_create_schema.sql       # Creación de esquema DW (p.ej. sales_ms)
│  │  ├─ 010_dim_cliente.sql
│  │  ├─ 011_dim_producto.sql
│  │  ├─ 012_dim_tiempo.sql
│  │  ├─ 020_fact_ventas.sql
│  │  ├─ 030_metas_ventas.sql        # Tabla de metas/objetivos comerciales
│  │  ├─ 040_indices.sql             # Índices, particiones (si aplica)
│  │  └─ seeds/                      # Datos de ejemplo para validar el modelo
│  └─ views/                         # Vistas consumibles por BI
├─ etl/
│  ├─ common/
│  │  ├─ currency.py                 # Conversión de moneda por fecha (p.ej. BCCR)
│  │  ├─ dates.py                    # Normalización/formato de fechas
│  │  ├─ gender.py                   # Estandarización de género/valores categóricos
│  │  └─ productos_bridge.py         # Mapeos entre SKUs/códigos
│  ├─ extract/
│  │  ├─ from_mssql.py               # Lectura desde SQL Server (origen transaccional si aplica)
│  │  ├─ from_mysql.py               # Lectura desde MySQL
│  │  ├─ from_mongo.py               # Lectura desde MongoDB
│  │  └─ from_neo4j.py               # Lectura desde Neo4j (consultas Cypher)
│  ├─ transform/
│  │  ├─ to_star_factventas.py       # Conforma el modelo estrella (hechos/dimensiones)
│  │  └─ build_dimensions.py         # Deduplicación, surrogate keys, SCD si aplica
│  ├─ load/
│  │  ├─ to_dw_mssql.py              # Carga en tablas del DW (bulk insert/merge)
│  │  └─ upsert_metas_ventas.py      # Carga/actualización de metas
│  ├─ jobs/
│  │  ├─ bccr_tc_historico.py        # Job para poblar tipo de cambio histórico
│  │  ├─ bccr_tc_diario.py           # Job programado diario (5:00 a.m., por ejemplo)
│  │  └─ scheduler.py                # Orquestación (APScheduler/cron)
│  └─ configs/
│     └─ connections.yaml            # Conexiones y credenciales (sin secretos en git)
├─ analytics/
│  ├─ powerbi/
│  │  ├─ dashboard_ventas.pbix       # Reporte Power BI
│  │  └─ dataset_config.md           # Origenes, medidas y roles de seguridad
│  └─ apriori/
│     ├─ notebooks/
│     │  └─ 01_apriori_exploracion.ipynb
│     ├─ pipeline.py                 # Genera reglas de asociación y persiste resultados
│     └─ serve_rules_api/
│        ├─ app.py                   # FastAPI: endpoints de recomendaciones
│        └─ models/                  # Esquemas/Pydantic
├─ services/
│  ├─ api-mongo/                     # CRUD de ventas/entidades sobre MongoDB
│  │  ├─ src/                        # Express+TS o FastAPI (a elección de stack)
│  │  ├─ tests/
│  │  └─ .env.example
│  ├─ api-neo4j/                     # CRUD de ventas/entidades sobre Neo4j
│  │  ├─ src/
│  │  ├─ tests/
│  │  └─ .env.example
│  ├─ api-supabase/                  # CRUD sobre Supabase (Postgres remoto)
│  │  ├─ src/
│  │  ├─ tests/
│  │  └─ .env.example                # SUPABASE_URL, SUPABASE_ANON_KEY, etc.
│  └─ api-loader-sql/                # API para cargas masivas a MS SQL y MySQL
│     ├─ src/                        # Endpoints para subir CSV/Parquet y ejecutar ingestas
│     ├─ tests/
│     └─ .env.example
├─ apps/                              # Frontends independientes (múltiples UIs)
│  ├─ web-mongo/                      # UI CRUD para MongoDB
│  ├─ web-neo4j/                      # UI CRUD para Neo4j
│  ├─ web-supabase/                   # UI CRUD para Supabase (DB remota)
│  └─ web-loader/                     # UI para cargas masivas a MS SQL/MySQL
├─ packages/                          # Paquetes reutilizables (monorepo)
│  ├─ ui/                             # Componentes React compartidos (Tailwind/shadcn)
│  ├─ schemas/                        # Tipos Zod/TS o Pydantic compartidos
│  └─ utils/                          # Helpers (formato de moneda, fechas, etc.)
├─ scripts/
│  ├─ dev_up.sh                       # Levanta stacks de desarrollo
│  ├─ etl_run_all.sh                  # Orquesta extract→transform→load
│  └─ seed_minimo.sh                  # Carga de datos mínima para demos
├─ .env.example                       # Variables globales (no secretos)
├─ package.json                       # pnpm workspaces para apps y servicios Node
├─ pnpm-workspace.yaml                # Define qué carpetas son paquetes del workspace
├─ pyproject.toml                     # Config Python (uv/poetry/pip-tools)
└─ turbo.json                         # Turborepo (pipelines de build/test/lint)
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
# MSSQL - Sales
MSSQL_SA_PASS=YourStrong@Passw0rd1
MSSQL_SA_PORT=1433

# MSSQL - Datawarehouse
MSSQL_DW_PASS=YourStrong@Passw0rd1
MSSQL_DW_PORT=1434

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
