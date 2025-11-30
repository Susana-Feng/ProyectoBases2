# ETLs & Jobs

Este paquete contiene extractores, transformaciones y cargas (ETL) y jobs programados usados por el proyecto.

## Resumen rápido
- Directorio principal: `etl/`
- Script de entrada: `main.py`
- ETLs implementados: MongoDB, MS SQL Server, MySQL, Supabase

## Fuentes de Datos

### Implementadas
- ✅ **MongoDB**: Base de datos de documentos con órdenes en CRC
- ✅ **MS SQL Server (DB_SALES)**: Base de datos transaccional con SKU oficial en USD
- ✅ **PostgreSQL/Supabase**: UUIDs, productos sin SKU (servicios)

### Pendientes
- ⏳ **MySQL**: Códigos alternos, precios en string, fechas en texto
- ⏳ **Neo4j**: Grafo de compras

## Idempotencia y Deduplicación

El proceso ETL está diseñado para ser **idempotente**: ejecutarlo múltiples veces NO duplicará datos.

### Mecanismos de deduplicación:
1. **Staging (stg.*)**: Usa sentencias `MERGE` de SQL Server para upsert
2. **DimCliente**: Verifica existencia antes de insertar (SourceSystem + SourceKey)
3. **DimProducto**: Solo inserta productos que no existan en el DW
4. **FactVentas**: Usa `NOT EXISTS` para evitar duplicados por SourceKey + Fuente
5. **DimTiempo**: Solo inserta fechas que no existan

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

### Ejecutar ETL filtrado por fuentes
Puedes limitar el proceso a una o varias bases usando `--db` (se puede repetir o pasar valores separados por coma). Ejemplos:

```bash
# Solo MS SQL Server
uv run python main.py --db mssql

# MySQL + Supabase
uv run python main.py --db mysql,supabase

# Todas las fuentes disponibles
uv run python main.py --db all
```

Si no se especifica `--db`, se procesan MS SQL Server, MySQL y Supabase por defecto.

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
│  ├─ mssql.py                # Extracción de MS SQL Server
│  ├─ mysql.py                # Extracción de MySQL
│  └─ supabase.py             # Extracción de Supabase/PostgreSQL
├─ load/
│  └─ general.py              # Carga al Data Warehouse
├─ transform/
│  ├─ mongo.py                # Transformación de datos de MongoDB
│  ├─ mssql.py                # Transformación de datos de MS SQL Server
│  ├─ mysql.py                # Transformación de datos de MySQL
│  └─ supabase.py             # Transformación de datos de Supabase
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

# MySQL - DB_SALES (fuente transaccional)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASS=YourPassword123!
MYSQL_DB=DB_SALES

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=sales_mongo

# BCCR WebService (tipos de cambio)
BCCR_TOKEN=your-token-here
BCCR_EMAIL=your-email@example.com
BCCR_NOMBRE=Your Name
```

## Tipos de Cambio (BCCR)

El sistema incluye integración con el WebService del BCCR para tipos de cambio:

### Carga Automática
- Al iniciar el ETL se verifica si existen tipos de cambio en `stg.tipo_cambio`
- Si no hay datos, se muestra una advertencia para que ejecutes el job SQL correspondiente

### Jobs en SQL Server
El script `40_bccr_jobs.sql` crea Stored Procedures en la BD:
- `jobs.sp_BCCR_SaveExchangeRate`: Guarda un tipo de cambio individual
- `jobs.sp_BCCR_SaveExchangeRateBatch`: Guarda múltiples tipos de cambio
- `jobs.sp_BCCR_GetMissingDates`: Obtiene fechas sin tipo de cambio
- `jobs.sp_BCCR_CheckStatus`: Verifica el estado de la carga
- `jobs.sp_BCCR_CargarTiposCambio`: Consume el WebService del BCCR para un rango de fechas
- Job de SQL Server Agent `BCCR_TipoCambio_Diario`: ejecuta `jobs.sp_BCCR_CargarHoy` a las 5:00 a.m.

### Ejecución Manual
Desde cualquier terminal con `sqlcmd` configurado:

```bash
# Cargar histórico (ajusta el rango según lo necesites)
sqlcmd -C -S <host>,<puerto> -U sa -P "<pass>" \
	-Q "EXEC DW_SALES.jobs.sp_BCCR_CargarTiposCambio @FechaInicio='2015-01-01', @FechaFinal=GETDATE();"

# Ejecutar la carga del día manualmente
sqlcmd -C -S <host>,<puerto> -U sa -P "<pass>" -Q "EXEC DW_SALES.jobs.sp_BCCR_CargarHoy;"

# Verificar estado
sqlcmd -C -S <host>,<puerto> -U sa -P "<pass>" -Q "EXEC DW_SALES.jobs.sp_BCCR_CheckStatus;"
```

### Configuración del Job Diario
Para programar la actualización diaria a las 5:00 AM:
1. **SQL Server Agent**: El script ya crea el job `BCCR_TipoCambio_Diario`
2. Si no tienes SQL Server Agent, ejecuta `jobs.sp_BCCR_CargarHoy` manualmente o configura tu propio programador externo que invoque el stored procedure

## Documentación Adicional

- **ETL MS SQL Server**: Ver `README_MSSQL_ETL.md` para documentación detallada
- **Instrucciones del proyecto**: Ver `../Instrucciones.md` en la raíz del proyecto
- **Esquemas de bases de datos**: Ver `../infra/docker/databases/`
