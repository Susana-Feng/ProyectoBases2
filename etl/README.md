# ETLs & Jobs

Este paquete contiene extractores, transformaciones y cargas (ETL) y jobs programados usados por el proyecto.

## Resumen rápido
- Directorio principal: `etl/`
- Script de entrada: `main.py`
- Jobs: `jobs/` (ej.: `bccr_tc_diario.py`, `bccr_tc_historico.py`, `scheduler.py`)
- ETLs implementados: MongoDB, MS SQL Server

## Fuentes de Datos

### Implementadas
- ✅ **MongoDB**: Base de datos de documentos con órdenes en CRC
- ✅ **MS SQL Server (DB_SALES)**: Base de datos transaccional con SKU oficial en USD

### Pendientes
- ⏳ **MySQL**: Códigos alternos, precios en string, fechas en texto
- ⏳ **PostgreSQL/Supabase**: UUIDs, productos sin SKU (servicios)
- ⏳ **Neo4j**: Grafo de compras

## Requisitos
- Python: la versión objetivo está en `.python-version` (por ejemplo 3.13+). Verifica con `python --version` o `python3 --version`.
- Recomendado: crear un entorno virtual para aislar dependencias.

## Instalación

```powershell
cd etl
uv sync          # instala dependencias de producción
uv sync --dev    # instala dependencias de desarrollo
```

### Variables de entorno
- Usa `.env.example` como plantilla. Hay un archivo ` .env.local` en el repositorio de ejemplo para desarrollo local.
- Antes de ejecutar, copia y edita:
```bash
cd etl
cp .env.example .env.local
# editar .env con tus credenciales/URLs
```

## Ejecución

### Ejecutar ETL completo
```bash
cd etl
uv run python main.py
```

Esto ejecutará:
1. Extracción de todas las fuentes implementadas (MongoDB, MS SQL Server)
2. Transformación y carga a staging
3. Carga al Data Warehouse (dimensiones y hechos)

### Ejecutar jobs individuales
```bash
# Cargar tipos de cambio históricos (3 años)
python -m jobs.bccr_tc_historico

# Actualizar tipo de cambio diario
python -m jobs.bccr_tc_diario

# Ejecutar scheduler (para jobs programados)
python -m jobs.scheduler
```

### Testing de ETL específico

**MS SQL Server:**
```bash
# Test completo
python test_mssql_etl.py

# Test de conexiones solamente
python test_mssql_etl.py --step connections

# Test de extracción solamente
python test_mssql_etl.py --step extract

# Resetear staging antes de ejecutar
python test_mssql_etl.py --reset
```

## Estructura del proyecto 
```bash
etl/
├─ configs/
│  └─ connections.py          # Configuración de conexiones a bases de datos
├─ extract/
│  ├─ mongo.py                # Extracción de MongoDB
│  └─ mssql.py                # Extracción de MS SQL Server
├─ jobs/
│  ├─ bccr_tc_diario.py       # Job diario de tipos de cambio
│  ├─ bccr_tc_historico.py    # Carga histórica de tipos de cambio
│  └─ scheduler.py            # Programador de jobs
├─ load/
│  └─ general.py              # Carga al Data Warehouse
├─ transform/
│  ├─ mongo.py                # Transformación de datos de MongoDB
│  └─ mssql.py                # Transformación de datos de MS SQL Server
├─ .env.example               # Template de variables de entorno
├─ .env.local                 # Variables de entorno locales (no versionado)
├─ main.py                    # Script principal ETL
├─ test_mssql_etl.py          # Testing del ETL de MS SQL Server
├─ README.md                  # Este archivo
├─ README_MSSQL_ETL.md        # Documentación detallada del ETL de MS SQL Server
└─ pyproject.toml             # Dependencias del proyecto
```

## Variables de Entorno

Copiar `.env.example` a `.env.local` y configurar:

```env
# Data Warehouse (MS SQL Server)
MSSQL_DW_HOST=localhost
MSSQL_DW_PORT=1433
MSSQL_DW_USER=sa
MSSQL_DW_PASS=YourPassword123!
MSSQL_DW_DB=DW_SALES

# MS SQL Server - DB_SALES (fuente transaccional)
MSSQL_SALES_HOST=localhost
MSSQL_SALES_PORT=1433
MSSQL_SALES_USER=sa
MSSQL_SALES_PASS=YourPassword123!
MSSQL_SALES_DB=DB_SALES

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=sales_mongo

# BCCR WebService (tipos de cambio)
BCCR_TOKEN=your-token-here
BCCR_EMAIL=your-email@example.com
BCCR_NOMBRE=Your Name
```

## Documentación Adicional

- **ETL MS SQL Server**: Ver `README_MSSQL_ETL.md` para documentación detallada
- **Instrucciones del proyecto**: Ver `../Instrucciones.md` en la raíz del proyecto
- **Esquemas de bases de datos**: Ver `../infra/docker/databases/`
