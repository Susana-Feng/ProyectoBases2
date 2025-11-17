/* =======================================================================
   Data Warehouse de Ventas — SQL Server (T-SQL)
   Estructura base + staging + modelo estrella + metas + analytics
   ======================================================================= */

-- 1) Base de datos (idempotente)
IF DB_ID('DW_SALES') IS NULL
BEGIN
  EXEC ('CREATE DATABASE DW_SALES');
END;
GO

-- Opcional: ajustar compatibilidad
ALTER DATABASE DW_SALES SET RECOVERY SIMPLE;
GO

USE DW_SALES;
GO

-- Configuraciones de sesión requeridas para índices filtrados
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
GO

/* =======================================================================
   2) Esquemas
   ======================================================================= */
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name='stg') EXEC('CREATE SCHEMA stg');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name='dw')  EXEC('CREATE SCHEMA dw');
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name='analytics') EXEC('CREATE SCHEMA analytics');
GO

/* =======================================================================
   3) Tablas de apoyo para ETL (staging)
   - map_producto: puente de equivalencias SKU / codigo_alt / codigo_mongo
   - tipo_cambio: TC por fecha y par de monedas
   - staging plano (opcional) para consolidar órdenes ítem a ítem
   ======================================================================= */

-- 3.1) Puente de equivalencias de producto
IF OBJECT_ID('stg.map_producto','U') IS NOT NULL DROP TABLE stg.map_producto;
CREATE TABLE stg.map_producto (
  map_id         INT IDENTITY(1,1) PRIMARY KEY,
  source_system  NVARCHAR(32)  NOT NULL,           -- 'mssql' | 'mysql' | 'pg' | 'mongo' | 'neo4j'
  source_code    NVARCHAR(128) NOT NULL,           -- SKU, codigo_alt, codigo_mongo, etc.
  sku_oficial    NVARCHAR(64)  NOT NULL,           -- clave canónica con la que poblar DimProducto
  nombre_norm    NVARCHAR(200) NULL,
  categoria_norm NVARCHAR(120) NULL,
  es_servicio    BIT           NULL,               -- p.ej. líneas sin SKU en Supabase
  CONSTRAINT UQ_map_producto UNIQUE (source_system, source_code)
);

-- 3.2) Tabla de tipos de cambio (para normalizar a USD por fecha de la orden)
IF OBJECT_ID('stg.tipo_cambio','U') IS NOT NULL DROP TABLE stg.tipo_cambio;
CREATE TABLE stg.tipo_cambio (
  fecha DATE       NOT NULL,
  de    CHAR(3)    NOT NULL,                       -- 'CRC', 'USD', etc.
  a     CHAR(3)    NOT NULL,                       -- 'USD' (target DW)
  tasa  DECIMAL(18,6) NOT NULL,                    -- monto en 'a' por 1 unidad de 'de'
  fuente NVARCHAR(64) NULL,                        -- e.g. 'BCCR WS'
  LoadTS DATETIME2(3) NOT NULL DEFAULT SYSDATETIME(), -- auditoría
  CONSTRAINT PK_tipo_cambio PRIMARY KEY (fecha, de, a)
);

-- 3.3) Staging plano de transacciones ítem-a-ítem (opcional pero útil)
IF OBJECT_ID('stg.orden_items','U') IS NOT NULL DROP TABLE stg.orden_items;
CREATE TABLE stg.orden_items (
  stg_id            BIGINT IDENTITY(1,1) PRIMARY KEY,
  source_system     NVARCHAR(32)  NOT NULL,        -- ms sql | mysql | pg | mongo | neo4j
  source_key_orden  NVARCHAR(128) NOT NULL,        -- id natural de la orden en la fuente
  source_key_item   NVARCHAR(128) NULL,            -- id natural del item si existe
  source_code_prod  NVARCHAR(128) NOT NULL,        -- SKU / codigo_alt / codigo_mongo
  cliente_key       NVARCHAR(128) NULL,            -- cliente_id
  fecha_raw         NVARCHAR(30)  NOT NULL,        -- fecha original del source (si venía como texto)
  canal_raw         NVARCHAR(32)  NULL,            -- WEB | TIENDA | APP | PARTNER | otros
  moneda            CHAR(3)       NOT NULL,        -- 'USD' | 'CRC'
  cantidad_raw      NVARCHAR(32)  NOT NULL,
  precio_unit_raw   NVARCHAR(32)  NOT NULL,
  total_raw         NVARCHAR(32)  NULL,
  -- Campos limpios (tras primer paso de limpieza)
  fecha_dt          DATE          NULL,         -- fecha de la orden ya casteada a Formato del DW
  cantidad_num      DECIMAL(18,4) NULL,
  precio_unit_num   DECIMAL(18,6) NULL,
  total_num         DECIMAL(18,6) NULL,
  load_ts           DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX IX_stg_items_fecha ON stg.orden_items(fecha_dt);
CREATE INDEX IX_stg_items_prod  ON stg.orden_items(source_code_prod);

-- 3.4) Staging Clientes
IF OBJECT_ID('stg.clientes','U') IS NOT NULL DROP TABLE stg.clientes;
CREATE TABLE stg.clientes (
  stg_id            BIGINT IDENTITY(1,1) PRIMARY KEY,
  source_system     NVARCHAR(32)  NOT NULL,        -- ms sql | mysql | pg | mongo | neo4j
  source_code  NVARCHAR(128) NOT NULL,              -- codigo cliente original
  cliente_email     NVARCHAR(150) NULL,
  cliente_nombre    NVARCHAR(200) NULL,
  genero_raw        NVARCHAR(20)  NULL,            -- Genero original (sin formatear)
  pais_raw          NVARCHAR(60)  NULL,
  fecha_creado_raw         NVARCHAR(30)  NOT NULL,        -- texto o datetime según fuente
  --- Campos limpios (tras primer paso de limpieza)
  fecha_creado_dt DATE NULL,
  genero_norm         CHAR(32)       NULL, 

  load_ts           DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME()
);

/* =======================================================================
   4) Dimensiones del DW (dw) — con claves sustitutas e historización simple
   - Se incluyen columnas de vigencia para SCD2 ligero (opcional en ETL)
   - Los dominios siguen las reglas de estandarización del documento
   ======================================================================= */

-- 4.1) DimTiempo: incluye TCs prácticos (CRC->USD y USD->CRC) por fecha
IF OBJECT_ID('dw.DimTiempo','U') IS NOT NULL DROP TABLE dw.DimTiempo;
CREATE TABLE dw.DimTiempo (
  TiempoID       INT          NOT NULL PRIMARY KEY, 
  Fecha          DATE         NOT NULL UNIQUE, -- YYYYMMDD
  Anio           INT          NOT NULL,
  Mes            TINYINT      NOT NULL,
  Dia            TINYINT      NOT NULL,
  -- TCs derivados de stg.tipo_cambio para acelerar consultas
  TC_CRC_USD     DECIMAL(18,6) NULL,                  -- USD por 1 CRC
  TC_USD_CRC     DECIMAL(18,6) NULL,                  -- CRC por 1 USD
  -- auditoría
  LoadTS         DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX IX_DimTiempo_YM ON dw.DimTiempo(Anio, Mes);

-- 4.2) DimCliente
IF OBJECT_ID('dw.DimCliente','U') IS NOT NULL DROP TABLE dw.DimCliente;
CREATE TABLE dw.DimCliente (
  ClienteID        INT IDENTITY(1,1) PRIMARY KEY,
  FechaCreacionID INT NOT NULL FOREIGN KEY REFERENCES dw.DimTiempo(TiempoID),
  -- claves de negocio (no únicas en DW para permitir SCD2)
  Email            NVARCHAR(150) NULL,
  Nombre           NVARCHAR(200) NOT NULL,
  Genero           NVARCHAR(32)  NOT NULL CHECK (Genero IN (N'Masculino',N'Femenino',N'No especificado')),
  Pais             NVARCHAR(60)  NULL,
  -- rastro de origen
  SourceSystem     NVARCHAR(32)  NULL,
  SourceKey        NVARCHAR(128) NULL,
  LoadTS           DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX IX_DimCliente_Email ON dw.DimCliente(Email) WHERE Email IS NOT NULL;

-- 4.3) DimProducto (canónica por sku_oficial)
IF OBJECT_ID('dw.DimProducto','U') IS NOT NULL DROP TABLE dw.DimProducto;
CREATE TABLE dw.DimProducto (
  ProductoID       INT IDENTITY(1,1) PRIMARY KEY,
  SKU              NVARCHAR(64)  NULL,     -- oficial (puede haber nulos transitorios mientras se mapea)
  Nombre           NVARCHAR(200) NOT NULL,
  Categoria        NVARCHAR(120) NOT NULL,
  EsServicio       BIT           NOT NULL DEFAULT 0,
  -- rastro de origen predominante
  SourceSystem     NVARCHAR(32)  NULL,
  SourceKey        NVARCHAR(128) NULL,
  LoadTS           DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME()
);
-- Unicidad blanda del SKU cuando está presente
CREATE UNIQUE INDEX UX_DimProducto_SKU ON dw.DimProducto(SKU) WHERE SKU IS NOT NULL;
CREATE INDEX IX_DimProducto_Categoria ON dw.DimProducto(Categoria);

/* =======================================================================
   5) Hechos (dw)
   - Normalizamos montos a USD
   - Conservamos moneda y total original + tasa aplicada para trazabilidad
   ======================================================================= */

IF OBJECT_ID('dw.FactVentas','U') IS NOT NULL DROP TABLE dw.FactVentas;
CREATE TABLE dw.FactVentas (
  FactID              BIGINT IDENTITY(1,1) PRIMARY KEY,
  -- FK a dimensiones
  TiempoID            INT         NOT NULL FOREIGN KEY REFERENCES dw.DimTiempo(TiempoID),
  ClienteID           INT         NOT NULL FOREIGN KEY REFERENCES dw.DimCliente(ClienteID),
  ProductoID          INT         NOT NULL FOREIGN KEY REFERENCES dw.DimProducto(ProductoID),
  -- atributos de análisis
  Canal               NVARCHAR(20) NOT NULL,                 -- WEB | TIENDA | APP | PARTNER
  Fuente              NVARCHAR(20) NOT NULL,                 -- 'mssql' | 'mysql' | 'pg' | 'mongo' | 'neo4j'
  -- medidas
  Cantidad            DECIMAL(18,4) NOT NULL,
  PrecioUnitUSD       DECIMAL(18,6) NOT NULL,                -- precio unitario normalizado a USD
  TotalUSD            DECIMAL(18,6) NOT NULL,                -- Total normalizado a USD
  -- trazabilidad y auditoría
  MonedaOriginal      CHAR(3)       NOT NULL,                -- 'USD' | 'CRC'
  PrecioUnitOriginal  DECIMAL(18,6) NULL,
  TotalOriginal       DECIMAL(18,6) NULL,
  LoadTS              DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX IX_FactVentas_Tiempo    ON dw.FactVentas(TiempoID);
CREATE INDEX IX_FactVentas_Producto  ON dw.FactVentas(ProductoID);
CREATE INDEX IX_FactVentas_Cliente   ON dw.FactVentas(ClienteID);
CREATE INDEX IX_FactVentas_Canal     ON dw.FactVentas(Canal);
CREATE INDEX IX_FactVentas_Fuente    ON dw.FactVentas(Fuente);

/* =======================================================================
   6) Metas de ventas (documento: MetasVentas conectada a DimCliente/DimProducto)
   ======================================================================= */

IF OBJECT_ID('dw.MetasVentas','U') IS NOT NULL DROP TABLE dw.MetasVentas;
CREATE TABLE dw.MetasVentas (
  MetaID     INT IDENTITY(1,1) PRIMARY KEY,
  ClienteID  INT NOT NULL FOREIGN KEY REFERENCES dw.DimCliente(ClienteID),
  ProductoID INT NOT NULL FOREIGN KEY REFERENCES dw.DimProducto(ProductoID),
  Anio       INT NOT NULL,
  Mes        INT NOT NULL CHECK (Mes BETWEEN 1 AND 12),
  MetaUSD    DECIMAL(18,2) NOT NULL,
  LoadTS     DATETIME2(3) NOT NULL DEFAULT SYSDATETIME(),
  CONSTRAINT UX_Metas_ClienteProdMes UNIQUE (ClienteID, ProductoID, Anio, Mes)
);
CREATE INDEX IX_Metas_AnioMes ON dw.MetasVentas(Anio, Mes);

/* =======================================================================
   7) Resultados de Apriori (para recomendaciones en webs transaccionales)
   ======================================================================= */

IF OBJECT_ID('analytics.AssociationRules','U') IS NOT NULL DROP TABLE analytics.AssociationRules;
CREATE TABLE analytics.AssociationRules (
  RuleID        BIGINT IDENTITY(1,1) PRIMARY KEY,
  Antecedent    NVARCHAR(450) NOT NULL,   -- lista de SKU canónicos separados por coma
  Consequent    NVARCHAR(450) NOT NULL,   -- lista de SKU canónicos
  Support       DECIMAL(9,6)   NOT NULL,
  Confidence    DECIMAL(9,6)   NOT NULL,
  Lift          DECIMAL(9,6)   NOT NULL,
  MinItems      INT            NULL,       -- metadatos opcionales
  MaxItems      INT            NULL,
  GeneratedAt   DATETIME2(3)   NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX IX_AR_Consequent ON analytics.AssociationRules(Consequent);

/* =======================================================================
   8) Vistas de conveniencia (opcionales)
   ======================================================================= */

-- Vista: Ventas agregadas por año-mes-producto
IF OBJECT_ID('dw.vw_VentasMensuales','V') IS NOT NULL DROP VIEW dw.vw_VentasMensuales;
GO
CREATE VIEW dw.vw_VentasMensuales AS
SELECT
  t.Anio,
  t.Mes,
  p.SKU,
  p.Nombre AS Producto,
  p.Categoria,
  SUM(f.Cantidad)   AS Qty,
  SUM(f.TotalUSD)   AS VentasUSD
FROM dw.FactVentas f
JOIN dw.DimTiempo  t ON t.TiempoID  = f.TiempoID
JOIN dw.DimProducto p ON p.ProductoID = f.ProductoID
GROUP BY t.Anio, t.Mes, p.SKU, p.Nombre, p.Categoria;
GO

/* =======================================================================
   9) Reglas prácticas para el llenado (comentarios de guía para el ETL)
   - Cargar DimTiempo 3+ años hacia atrás y adelante según calendario académico
   - Poblar TC desde stg.tipo_cambio en DimTiempo (por fecha)
   ======================================================================= */
