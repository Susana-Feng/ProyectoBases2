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
   1.5) Limpieza de tablas existentes (en orden correcto de dependencias)
   ======================================================================= */
-- Primero: Tablas de hechos y analytics (dependen de dimensiones)
IF OBJECT_ID('analytics.AssociationRules','U') IS NOT NULL DROP TABLE analytics.AssociationRules;
IF OBJECT_ID('dw.MetasVentas','U') IS NOT NULL DROP TABLE dw.MetasVentas;
IF OBJECT_ID('dw.FactVentas','U') IS NOT NULL DROP TABLE dw.FactVentas;

-- Segundo: Dimensiones que dependen de otras dimensiones
IF OBJECT_ID('dw.DimCliente','U') IS NOT NULL DROP TABLE dw.DimCliente;
IF OBJECT_ID('dw.DimProducto','U') IS NOT NULL DROP TABLE dw.DimProducto;

-- Tercero: Dimensiones base
IF OBJECT_ID('dw.DimTiempo','U') IS NOT NULL DROP TABLE dw.DimTiempo;

-- Cuarto: Tablas de staging
IF OBJECT_ID('stg.orden_items','U') IS NOT NULL DROP TABLE stg.orden_items;
IF OBJECT_ID('stg.clientes','U') IS NOT NULL DROP TABLE stg.clientes;
IF OBJECT_ID('stg.tipo_cambio','U') IS NOT NULL DROP TABLE stg.tipo_cambio;
IF OBJECT_ID('stg.map_producto','U') IS NOT NULL DROP TABLE stg.map_producto;
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
CREATE TABLE stg.tipo_cambio (
  fecha DATE       NOT NULL,
  de    CHAR(3)    NOT NULL,                       -- 'CRC', 'USD', etc.
  a     CHAR(3)    NOT NULL,                       -- 'USD' (target DW)
  tasa  DECIMAL(18,6) NOT NULL,                    -- valor publicado por el BCCR (CRC por USD)
  fuente NVARCHAR(64) NULL,                        -- e.g. 'BCCR WS'
  LoadTS DATETIME2(3) NOT NULL DEFAULT SYSDATETIME(), -- auditoría
  CONSTRAINT PK_tipo_cambio PRIMARY KEY (fecha, de, a)
);

-- 3.3) Staging plano de transacciones ítem-a-ítem (opcional pero útil)
CREATE TABLE stg.orden_items (
  stg_id            BIGINT IDENTITY(1,1) PRIMARY KEY,
  source_system     NVARCHAR(32)  NOT NULL,        -- ms sql | mysql | pg | mongo | neo4j
  source_key_orden  NVARCHAR(128) NOT NULL,        -- id natural de la orden en la fuente
  source_key_item   NVARCHAR(128) NULL,            -- id natural del item si existe
  source_code_prod  NVARCHAR(128) NOT NULL,        -- SKU / codigo_alt / codigo_mongo
  cliente_key       NVARCHAR(128) NULL,            -- cliente_id
  fecha_raw         NVARCHAR(50)  NOT NULL,        -- fecha original del source (si venía como texto)
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
CREATE TABLE dw.DimTiempo (
  TiempoID       INT          NOT NULL PRIMARY KEY, 
  Fecha          DATE         NOT NULL UNIQUE, -- YYYYMMDD
  Anio           INT          NOT NULL,
  Mes            TINYINT      NOT NULL,
  Dia            TINYINT      NOT NULL,
  -- TCs derivados de stg.tipo_cambio para acelerar consultas (valores BCCR en CRC por USD)
  TC_CRC_USD     DECIMAL(18,6) NULL,                  -- Tasa de compra (CRC por USD)
  TC_USD_CRC     DECIMAL(18,6) NULL,                  -- Tasa de venta (CRC por USD)
  -- auditoría
  LoadTS         DATETIME2(3)  NOT NULL DEFAULT SYSDATETIME()
);
CREATE INDEX IX_DimTiempo_YM ON dw.DimTiempo(Anio, Mes);

-- 4.2) DimCliente
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

CREATE TABLE dw.FactVentas (
  FactID              BIGINT IDENTITY(1,1) PRIMARY KEY,
  -- FK a dimensiones
  TiempoID            INT         NOT NULL FOREIGN KEY REFERENCES dw.DimTiempo(TiempoID),
  ClienteID           INT         NOT NULL FOREIGN KEY REFERENCES dw.DimCliente(ClienteID),
  ProductoID          INT         NOT NULL FOREIGN KEY REFERENCES dw.DimProducto(ProductoID),
  -- atributos de análisis
  Canal               NVARCHAR(20) NOT NULL,                 -- WEB | TIENDA | APP | PARTNER
  Fuente              NVARCHAR(20) NOT NULL,                 -- 'mssql' | 'mysql' | 'pg' | 'mongo' | 'neo4j'
  SourceKey        NVARCHAR(128) NULL,                     -- id original de la orden
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

CREATE TABLE analytics.AssociationRules (
  RuleID        BIGINT IDENTITY(1,1) PRIMARY KEY,
  Antecedent    NVARCHAR(450) NOT NULL,   -- lista de SKU canónicos
  Consequent    NVARCHAR(450) NOT NULL,   -- lista de SKU canónicos
  Support       DECIMAL(9,6)   NOT NULL,
  Confidence    DECIMAL(9,6)   NOT NULL,
  Lift          DECIMAL(9,6)   NOT NULL,
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

-- Vista: Transacciones con lista de ítems (para reglas de asociación)
-- IMPORTANT: SourceKey format is "ordenId-itemId", we need to group by ordenId only
-- to get all items in a single transaction for Apriori algorithm
IF OBJECT_ID('dw.vw_Transacciones','V') IS NOT NULL DROP VIEW dw.vw_Transacciones;
GO
CREATE VIEW dw.vw_Transacciones AS
SELECT
    -- Extract only the order part from SourceKey (before the last hyphen-separated segment)
    -- Handles: mssql/mysql "1000-2926", mongo "objId-objId", supabase "uuid-uuid", neo4j "ORD-XXX-SKU-YYY"
    CASE 
        WHEN V.Fuente = 'neo4j' THEN 
            -- neo4j format: ORD-000001-SKU-1133 -> extract ORD-000001
            LEFT(V.SourceKey, CHARINDEX('-SKU-', V.SourceKey) - 1)
        WHEN V.Fuente IN ('mongo') THEN 
            -- mongo ObjectId format: 24 chars each, separated by hyphen
            LEFT(V.SourceKey, 24)
        WHEN V.Fuente = 'supabase' THEN 
            -- supabase UUID format: 36 chars each, separated by hyphen
            LEFT(V.SourceKey, 36)
        ELSE 
            -- mssql/mysql format: ordenId-itemId, extract ordenId (before last hyphen)
            LEFT(V.SourceKey, LEN(V.SourceKey) - CHARINDEX('-', REVERSE(V.SourceKey)))
    END AS transaction_id,
    STRING_AGG(P.SKU, ', ') WITHIN GROUP (ORDER BY P.SKU) AS item
FROM dw.FactVentas AS V
INNER JOIN dw.DimProducto P ON V.ProductoID = P.ProductoID
WHERE P.SKU IS NOT NULL AND P.SKU != ''  -- Only include products with valid SKUs
GROUP BY 
    CASE 
        WHEN V.Fuente = 'neo4j' THEN LEFT(V.SourceKey, CHARINDEX('-SKU-', V.SourceKey) - 1)
        WHEN V.Fuente IN ('mongo') THEN LEFT(V.SourceKey, 24)
        WHEN V.Fuente = 'supabase' THEN LEFT(V.SourceKey, 36)
        ELSE LEFT(V.SourceKey, LEN(V.SourceKey) - CHARINDEX('-', REVERSE(V.SourceKey)))
    END
GO

/* =======================================================================
   9) Stored Procedures
   ======================================================================= */

-- 9.1) Obtener los principales 5 consecuentes para una lista dada de SKUs
IF OBJECT_ID('dw.sp_obtener_consecuentes_por_skus','P') IS NOT NULL
    DROP PROCEDURE dw.sp_obtener_consecuentes_por_skus;
GO

CREATE OR ALTER PROCEDURE dw.sp_obtener_consecuentes_por_skus
    @lista_skus NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;

    CREATE TABLE #skus_entrada (sku NVARCHAR(50) PRIMARY KEY);
    
    INSERT INTO #skus_entrada (sku)
    SELECT DISTINCT LTRIM(RTRIM(value)) 
    FROM STRING_SPLIT(@lista_skus, ',')
    WHERE LTRIM(RTRIM(value)) <> '';

    WITH ReglasFiltradas AS (
        SELECT 
            r.RuleID,
            r.Antecedent,
            r.Consequent,
            r.Support,
            r.Confidence,
            r.Lift,
            (SELECT COUNT(DISTINCT LTRIM(RTRIM(value)))
             FROM STRING_SPLIT(REPLACE(REPLACE(r.Antecedent, '(', ''), ')', ''), ',') 
             WHERE LTRIM(RTRIM(value)) <> '') as total_antecedentes,
            (SELECT COUNT(DISTINCT LTRIM(RTRIM(value)))
             FROM STRING_SPLIT(REPLACE(REPLACE(r.Antecedent, '(', ''), ')', ''), ',') a
             INNER JOIN #skus_entrada se ON LTRIM(RTRIM(a.value)) = se.sku
             WHERE LTRIM(RTRIM(a.value)) <> '') as antecedentes_en_lista,
            (SELECT COUNT(*) FROM #skus_entrada) as total_en_lista,
            (SELECT COUNT(*)
             FROM STRING_SPLIT(REPLACE(REPLACE(r.Consequent, '(', ''), ')', ''), ',') c
             INNER JOIN #skus_entrada se ON LTRIM(RTRIM(c.value)) = se.sku
             WHERE LTRIM(RTRIM(c.value)) <> '') as consecuentes_en_lista,
            -- Incluir SKU, Nombre y CodigoMongo para antecedentes
            (SELECT dp.SKU, dp.Nombre, mp.source_code AS CodigoMongo
             FROM dw.DimProducto dp
             INNER JOIN #skus_entrada se ON dp.SKU = se.sku
             LEFT JOIN stg.map_producto mp ON dp.SKU = mp.sku_oficial AND mp.source_system = 'mongo'
             FOR JSON PATH) AS source_keys_antecedentes,
            -- Incluir SKU, Nombre y CodigoMongo para consecuentes
            (SELECT DISTINCT dp.SKU, dp.Nombre, mp.source_code AS CodigoMongo
             FROM STRING_SPLIT(REPLACE(REPLACE(r.Consequent, '(', ''), ')', ''), ',') c
             INNER JOIN dw.DimProducto dp ON LTRIM(RTRIM(c.value)) = dp.SKU
             LEFT JOIN stg.map_producto mp ON dp.SKU = mp.sku_oficial AND mp.source_system = 'mongo'
             WHERE LTRIM(RTRIM(c.value)) <> ''
             FOR JSON PATH) AS source_keys_consecuentes
        FROM analytics.AssociationRules r
    )
    SELECT TOP 5
        Antecedent,
        Consequent,
        Support,
        Confidence,
        Lift,
        source_keys_antecedentes AS SourceKeysAntecedentes,
        source_keys_consecuentes AS SourceKeysConsecuentes
    FROM ReglasFiltradas
    WHERE total_antecedentes > 0 
        AND antecedentes_en_lista = total_antecedentes
        AND total_en_lista = total_antecedentes
        AND consecuentes_en_lista = 0
    ORDER BY Confidence DESC, Lift DESC;

    DROP TABLE #skus_entrada;
END;
GO

-- 9.2) Obtener SKUs equivalentes a una lista de códigos MongoDB
-- Usa map_producto para encontrar el SKU canónico a partir del codigo_mongo
IF OBJECT_ID('dw.sp_obtener_skus_por_codigos_mongo','P') IS NOT NULL
    DROP PROCEDURE dw.sp_obtener_skus_por_codigos_mongo;
GO
CREATE OR ALTER PROCEDURE dw.sp_obtener_skus_por_codigos_mongo
    @lista_codigos_mongo NVARCHAR(MAX)
AS
BEGIN
    SET NOCOUNT ON;

    -- Tabla temporal para códigos MongoDB de entrada
    CREATE TABLE #codigos_mongo (codigo_mongo NVARCHAR(128) PRIMARY KEY);
    
    -- Insertar y limpiar los códigos MongoDB
    INSERT INTO #codigos_mongo (codigo_mongo)
    SELECT DISTINCT LTRIM(RTRIM(value)) 
    FROM STRING_SPLIT(@lista_codigos_mongo, ',')
    WHERE LTRIM(RTRIM(value)) <> '';

    -- Consulta para obtener los SKUs equivalentes via map_producto
    -- El codigo_mongo está en map_producto con source_system = 'mongo'
    SELECT 
        cm.codigo_mongo AS CodigoMongo,
        COALESCE(mp.sku_oficial, dp.SKU) AS SKU
    FROM #codigos_mongo cm
    LEFT JOIN stg.map_producto mp 
        ON cm.codigo_mongo = mp.source_code 
        AND mp.source_system = 'mongo'
    LEFT JOIN dw.DimProducto dp 
        ON cm.codigo_mongo = dp.SourceKey 
        AND dp.SourceSystem = 'mongo'
    WHERE COALESCE(mp.sku_oficial, dp.SKU) IS NOT NULL
    ORDER BY SKU, cm.codigo_mongo;

    -- Limpiar tabla temporal
    DROP TABLE #codigos_mongo;
END;

GO
