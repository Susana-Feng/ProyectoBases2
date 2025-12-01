# ETL - Data Warehouse de Ventas

Este módulo contiene el proceso ETL (Extract, Transform, Load) que integra datos de múltiples fuentes transaccionales heterogéneas en un Data Warehouse central en SQL Server.

## Arquitectura General

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   MS SQL    │  │    MySQL    │  │  Supabase   │  │   MongoDB   │  │    Neo4j    │
│  (DB_SALES) │  │  (DB_SALES) │  │ (PostgreSQL)│  │  (tiendaDB) │  │   (Graph)   │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │                │
       ▼                ▼                ▼                ▼                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         [1] EXTRACT (extract/*.py)                               │
│  Extraer productos, clientes, órdenes y detalles de cada fuente                 │
└──────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    [2] BUILD EQUIVALENCES (equivalences.py)                      │
│                                                                                  │
│  Construir mapa de equivalencias de productos ANTES de transformar:             │
│  • Agrupar productos por (nombre, categoría) de TODAS las fuentes               │
│  • Para cada grupo, determinar el SKU usando prioridad:                          │
│    1. MSSQL SKU (canónico)                                                       │
│    2. Supabase SKU                                                               │
│    3. MongoDB equivalencias.sku                                                  │
│    4. Neo4j sku                                                                  │
│    5. Generar nuevo SKU                                                          │
└──────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         [3] TRANSFORM (transform/*.py)                           │
│  Cada fuente consulta el mapa de equivalencias para obtener el SKU correcto     │
│  • Normalización de géneros, fechas, montos                                      │
│  • Registro en stg.map_producto con el SKU resuelto                              │
└──────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              STAGING (stg.*)                                     │
│  • stg.clientes        - Clientes normalizados de todas las fuentes             │
│  • stg.map_producto    - Tabla puente de equivalencias SKU ↔ códigos            │
│  • stg.orden_items     - Ítems de órdenes normalizados                          │
│  • stg.tipo_cambio     - Tipos de cambio CRC/USD del BCCR                       │
└──────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          [4] LOAD (load/general.py)                              │
│  Carga al Data Warehouse con modelo estrella                                     │
└──────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            DATA WAREHOUSE (dw.*)                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                          │
│  │ DimCliente  │───▶│ FactVentas  │◀───│ DimProducto │                          │
│  └─────────────┘    └──────┬──────┘    └─────────────┘                          │
│                            │                                                     │
│                     ┌──────▼──────┐                                             │
│                     │  DimTiempo  │                                             │
│                     └─────────────┘                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Fuentes de Datos y Heterogeneidades

El ETL integra 5 fuentes de datos con diferentes formatos y estructuras:

| Fuente | Código Producto | Moneda | Género | Fechas | Montos |
|--------|-----------------|--------|--------|--------|--------|
| **MS SQL Server** | SKU (oficial) | USD | Masculino/Femenino | DATETIME2 | DECIMAL |
| **MySQL** | codigo_alt | USD/CRC | M/F/X | VARCHAR | VARCHAR con comas |
| **Supabase** | SKU (puede estar vacío) | USD/CRC | M/F | TIMESTAMPTZ | NUMERIC |
| **MongoDB** | codigo_mongo + equivalencias | CRC (enteros) | Masculino/Femenino/Otro | ISODate | INT |
| **Neo4j** | sku + codigo_alt + codigo_mongo | USD/CRC | M/F/Otro/Masculino/Femenino | datetime | FLOAT |

## Sistema de Mapeo de Productos

### El Problema

Cada fuente usa diferentes códigos para identificar productos:
- MSSQL usa `SKU` (oficial)
- MySQL usa `codigo_alt`
- Supabase usa `SKU` (puede estar vacío)
- MongoDB usa `codigo_mongo` + campo `equivalencias.sku`
- Neo4j tiene todos los códigos (`sku`, `codigo_alt`, `codigo_mongo`)

Un mismo producto puede existir en múltiples fuentes con diferentes códigos. El reto es asignar un **SKU único** a cada producto.

### La Solución: Mapa de Equivalencias

**ANTES de transformar**, el ETL construye un mapa de equivalencias analizando los productos de **TODAS las fuentes**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASE DE EQUIVALENCIAS                                │
│                                                                             │
│  1. Extraer productos de todas las fuentes                                  │
│  2. Agrupar por (nombre, categoría) - case insensitive                      │
│  3. Para cada grupo, buscar el mejor SKU:                                   │
│     ├─► ¿MSSQL tiene SKU? → Usar ese (prioridad 1)                         │
│     ├─► ¿Supabase tiene SKU? → Usar ese (prioridad 2)                      │
│     ├─► ¿MongoDB tiene equivalencias.sku? → Usar ese (prioridad 3)         │
│     ├─► ¿Neo4j tiene sku? → Usar ese (prioridad 4)                         │
│     └─► Ninguno tiene SKU → Generar nuevo (SKU-XXXX)                       │
│  4. Resultado: Mapa (nombre, categoria) → SKU oficial                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tabla `stg.map_producto`

```sql
stg.map_producto
├── source_system   -- 'mssql' | 'mysql' | 'supabase' | 'mongo' | 'neo4j'
├── source_code     -- SKU, codigo_alt, codigo_mongo, UUID, etc.
├── sku_oficial     -- Clave canónica para DimProducto
├── nombre_norm     -- Nombre normalizado del producto
├── categoria_norm  -- Categoría normalizada
└── es_servicio     -- TRUE si es un servicio (sin SKU físico)
```

### Ejemplos de Mapeo

**Caso 1: Producto existe en MSSQL (fuente canónica)**
```
Extracción:
  MSSQL:    SKU="SKU-1000", nombre="Televisor LED 32", categoria="Electrónica"
  MySQL:    codigo_alt="ALT-AB12", nombre="Televisor LED 32", categoria="Electrónica"
  MongoDB:  codigo_mongo="MN-4000", equivalencias.sku="SKU-1000", nombre="Televisor LED 32"
  Neo4j:    sku="SKU-1000", codigo_alt="ALT-AB12", codigo_mongo="MN-4000"

Fase de Equivalencias:
  └─► Agrupar por ("televisor led 32", "electrónica")
  └─► MSSQL tiene SKU="SKU-1000" → Usar ese (prioridad 1)
  └─► Resultado: sku_oficial = "SKU-1000"

Transformación:
  └─► MSSQL registra: (mssql, "1", "SKU-1000", "Televisor LED 32", "Electrónica")
  └─► MySQL registra: (mysql, "ALT-AB12", "SKU-1000", "Televisor LED 32", "Electrónica")
  └─► MongoDB registra: (mongo, "MN-4000", "SKU-1000", "Televisor LED 32", "Electrónica")
  └─► Neo4j registra: (neo4j, "SKU-1000", "SKU-1000", "Televisor LED 32", "Electrónica")
```

**Caso 2: Producto NO existe en MSSQL, pero tiene equivalencias.sku en MongoDB**
```
Extracción:
  MySQL:    codigo_alt="ALT-ZZ99", nombre="Producto Especial", categoria="Especial"
  MongoDB:  codigo_mongo="MN-9999", equivalencias.sku="SKU-2000", nombre="Producto Especial"

Fase de Equivalencias:
  └─► Agrupar por ("producto especial", "especial")
  └─► MSSQL: No tiene este producto
  └─► Supabase: No tiene este producto
  └─► MongoDB tiene equivalencias.sku="SKU-2000" → Usar ese (prioridad 3)
  └─► Resultado: sku_oficial = "SKU-2000"

Transformación:
  └─► MySQL registra: (mysql, "ALT-ZZ99", "SKU-2000", "Producto Especial", "Especial")
  └─► MongoDB registra: (mongo, "MN-9999", "SKU-2000", "Producto Especial", "Especial")
```

**Caso 3: Producto solo existe en MySQL (sin SKU en ninguna fuente)**
```
Extracción:
  MySQL:    codigo_alt="ALT-NEW1", nombre="Producto Nuevo", categoria="Nueva"

Fase de Equivalencias:
  └─► Agrupar por ("producto nuevo", "nueva")
  └─► Ninguna fuente tiene SKU
  └─► Generar nuevo: SKU-0501
  └─► Resultado: sku_oficial = "SKU-0501"

Transformación:
  └─► MySQL registra: (mysql, "ALT-NEW1", "SKU-0501", "Producto Nuevo", "Nueva")
```

**Caso 4: Servicio en Supabase (sin SKU físico)**
```
Extracción:
  Supabase: producto_id="uuid-xxxx", sku=NULL, nombre="Consultoría", categoria="Servicios"

Fase de Equivalencias:
  └─► Agrupar por ("consultoría", "servicios")
  └─► Ninguna fuente tiene SKU
  └─► Generar nuevo: SKU-0502, marcar es_servicio=TRUE
  └─► Resultado: sku_oficial = "SKU-0502"

Transformación:
  └─► Supabase registra: (supabase, "uuid-xxxx", "SKU-0502", "Consultoría", "Servicios", es_servicio=TRUE)
```

### Principio Clave

> **El mapa de equivalencias se construye ANTES de la transformación usando información de TODAS las fuentes.**
> 
> Esto garantiza que:
> - Si MongoDB tiene `equivalencias.sku`, ese SKU se usa incluso si MySQL se procesa primero
> - Productos idénticos en diferentes fuentes siempre obtienen el mismo SKU
> - Solo se generan SKUs nuevos cuando NINGUNA fuente tiene uno

## Normalización de Datos

### Género
```
M | Masculino       → "Masculino"
F | Femenino        → "Femenino"
X | Otro | NULL     → "No especificado"
```

### Moneda
- **USD**: Se usa directamente
- **CRC**: Se convierte a USD usando el tipo de cambio de `stg.tipo_cambio` para la fecha de la orden

### Fechas
- Todas las fechas se convierten a `DATE` para `DimTiempo`
- Se usa el formato `YYYYMMDD` como `TiempoID`

### Canales
```
WEB | TIENDA | APP | PARTNER → Se normalizan a mayúsculas
```

## Idempotencia y Deduplicación

El proceso ETL está diseñado para ser **idempotente**: ejecutarlo múltiples veces NO duplicará datos.

### Mecanismos de Deduplicación

| Componente | Mecanismo |
|------------|-----------|
| **Staging (stg.*)** | Sentencias `MERGE` de SQL Server para upsert |
| **DimCliente** | Verifica existencia antes de insertar (`SourceSystem + SourceKey`) |
| **DimProducto** | Solo inserta productos con SKU que no existan |
| **FactVentas** | Usa `NOT EXISTS` para evitar duplicados (`SourceKey + Fuente`) |
| **DimTiempo** | Solo inserta fechas que no existan |

## Tipos de Cambio (BCCR)

El sistema obtiene tipos de cambio del Banco Central de Costa Rica para convertir CRC a USD:

### Tabla `stg.tipo_cambio`
```sql
├── fecha    -- Fecha del tipo de cambio
├── de       -- Moneda origen ('CRC' o 'USD')
├── a        -- Moneda destino ('USD' o 'CRC')
├── tasa     -- Valor del tipo de cambio
└── fuente   -- 'BCCR WS'
```

### Jobs Disponibles
- `jobs.sp_BCCR_CargarTiposCambio`: Carga tipos de cambio para un rango de fechas
- `jobs.sp_BCCR_CargarHoy`: Carga el tipo de cambio del día actual
- `jobs.sp_BCCR_CheckStatus`: Verifica el estado de la carga
- Job de SQL Server Agent `BCCR_TipoCambio_Diario`: Ejecuta automáticamente a las 5:00 AM

### Sincronización con DimTiempo
Durante la carga del DW, los tipos de cambio se sincronizan automáticamente desde `stg.tipo_cambio` a las columnas `TC_CRC_USD` y `TC_USD_CRC` en `DimTiempo`.

## Reglas de Asociación (Apriori)

Después de cargar el DW, el ETL ejecuta el algoritmo FP-Growth para descubrir patrones de compra:

```
┌─────────────────────────────────────────────────────────────────┐
│                    association_rules/                           │
│  ├── get_rules.py     - Ejecuta FP-Growth sobre FactVentas     │
│  └── load_rules.py    - Carga reglas a analytics.AssociationRules │
└─────────────────────────────────────────────────────────────────┘
```

Las reglas generadas se almacenan en `analytics.AssociationRules` y son consumidas por las aplicaciones web para mostrar recomendaciones de productos.

## Ejecución

### ETL Completo
```bash
uv run python main.py
```

### Filtrar por Fuentes
```bash
# Solo MS SQL Server
uv run python main.py --db mssql

# MySQL + Supabase
uv run python main.py --db mysql,supabase

# Todas las fuentes
uv run python main.py --db all
```

### Modo Debug
```bash
# Ver información detallada sobre el mapeo de productos
uv run python main.py --log-level debug
```

### Salida Típica
```
ETL - Sources: mssql, mysql, supabase, mongo, neo4j

[1] Exchange rates
    1095 records OK

[2] Extraction
    mssql: 600 clients | 450 products | 5000 orders | 12500 details
    mysql: 600 clients | 425 products | 5000 orders | 12000 details
    supab: 600 clients | 375 products | 5000 orders | 11500 details
    mongo: 600 clients | 350 products | 5000 orders
    neo4j: 600 clients | 400 products | 5000 orders

[3] Building product equivalences
    500 unique products across all sources
    SKU sources: MSSQL=450, Supabase=20, Mongo=15, Neo4j=10, Generated=5

[4] Transformation
    mssql: 600 clients | 450 products | 12500 items
    mysql: 600 clients | 425 products | 12000 items
    supab: 600 clients | 375 products | 11500 items
    mongo: 600 clients | 350 products | 11000 items
    neo4j: 600 clients | 400 products | 10500 items

[5] Load to Data Warehouse
    DimTiempo: up to date
    DimCliente: 3000 loaded
    DimProducto: 500 loaded
    FactVentas: 57500 loaded

[6] Association Rules (Apriori/FP-Growth)
    Generated 150 rules with min_support=0.01, min_confidence=0.3

ETL completed successfully
```

## Estructura del Proyecto

```
etl/
├── configs/
│   └── connections.py           # Configuración de conexiones a BD
├── extract/
│   ├── mongo.py                 # Extracción de MongoDB
│   ├── mssql.py                 # Extracción de MS SQL Server
│   ├── mysql.py                 # Extracción de MySQL
│   ├── neo4j.py                 # Extracción de Neo4j
│   └── supabase.py              # Extracción de Supabase/PostgreSQL
├── equivalences.py              # ⭐ Construcción del mapa de equivalencias
├── transform/
│   ├── mongo.py                 # Transformación MongoDB → Staging
│   ├── mssql.py                 # Transformación MSSQL → Staging
│   ├── mysql.py                 # Transformación MySQL → Staging
│   ├── neo4j.py                 # Transformación Neo4j → Staging
│   └── supabase.py              # Transformación Supabase → Staging
├── load/
│   └── general.py               # Carga Staging → Data Warehouse
├── association_rules/
│   ├── get_rules.py             # Generación de reglas con FP-Growth
│   └── load_rules.py            # Carga de reglas a analytics.*
├── main.py                      # Script principal del ETL
├── pyproject.toml               # Dependencias del proyecto
└── README.md                    # Este archivo
```

## Modelo del Data Warehouse

### Dimensiones

**DimCliente**
```sql
├── ClienteID (PK, IDENTITY)
├── SourceSystem        -- Fuente origen
├── SourceKey           -- ID original en la fuente
├── Email, Nombre, Genero, Pais
├── FechaCreacionID     -- FK a DimTiempo
└── LoadTS              -- Timestamp de carga
```

**DimProducto**
```sql
├── ProductoID (PK, IDENTITY)
├── SKU                 -- Código único canónico
├── Nombre, Categoria
├── EsServicio          -- TRUE si no tiene SKU físico
├── SourceSystem, SourceKey
└── LoadTS
```

**DimTiempo**
```sql
├── TiempoID (PK)       -- Formato YYYYMMDD
├── Fecha, Anio, Mes, Dia
├── TC_CRC_USD          -- Tipo de cambio CRC→USD
├── TC_USD_CRC          -- Tipo de cambio USD→CRC
└── LoadTS
```

### Tabla de Hechos

**FactVentas**
```sql
├── VentaID (PK, IDENTITY)
├── TiempoID (FK)       -- Fecha de la venta
├── ClienteID (FK)      -- Cliente que compró
├── ProductoID (FK)     -- Producto vendido
├── Canal, Fuente       -- Canal de venta y sistema origen
├── Cantidad            -- Unidades vendidas
├── PrecioUnitUSD       -- Precio unitario en USD
├── TotalUSD            -- Total de la línea en USD
├── MonedaOriginal      -- 'USD' o 'CRC'
├── PrecioUnitOriginal  -- Precio en moneda original
├── TotalOriginal       -- Total en moneda original
├── SourceKey           -- ID compuesto para deduplicación
└── LoadTS
```

## Documentación Adicional

- **Instrucciones del proyecto**: `../Instrucciones.md`
- **Esquemas de bases de datos**: `../infra/docker/databases/`
- **Generación de datos de prueba**: `../data/README.md`
