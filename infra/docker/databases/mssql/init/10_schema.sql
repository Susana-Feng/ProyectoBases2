/* ================================================================
 Script para crear el esquema en MS SQL Server
 Esquema: sales_ms
 Normalización: BCNF (Boyce-Codd Normal Form)
 Heterogeneidades:
 - Género: 'Masculino', 'Femenino'
 - Moneda: Siempre 'USD'
 - SKU: 'SKU oficial'
================================================================
*/

USE sales_db;
GO

-- Eliminar el esquema si existe (con todas sus tablas)
IF EXISTS (SELECT * FROM sys.schemas WHERE name = 'sales_ms')
BEGIN
    DROP SCHEMA sales_ms;
END
GO

-- Crear el esquema 'sales_ms'
CREATE SCHEMA sales_ms;
GO

-- ========= TABLAS DE CATÁLOGOS (Normalización 1FN - Valores Atómicos) =========

-- Tabla de Géneros (Catálogo)
CREATE TABLE sales_ms.Genero (
    GeneroId TINYINT PRIMARY KEY,
    Nombre NVARCHAR(20) NOT NULL UNIQUE,
    Descripcion NVARCHAR(100)
);

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla catálogo de géneros disponibles', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Genero';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único del género (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Genero', @level2type = N'COLUMN', @level2name = N'GeneroId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Nombre del género', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Genero', @level2type = N'COLUMN', @level2name = N'Nombre';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Descripción del género', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Genero', @level2type = N'COLUMN', @level2name = N'Descripcion';
GO

-- Tabla de Países (Catálogo)
CREATE TABLE sales_ms.Pais (
    PaisId INT IDENTITY PRIMARY KEY,
    Nombre NVARCHAR(80) NOT NULL UNIQUE,
    CodigoISO CHAR(2) UNIQUE
);

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla catálogo de países', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Pais';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único del país (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Pais', @level2type = N'COLUMN', @level2name = N'PaisId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Nombre del país', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Pais', @level2type = N'COLUMN', @level2name = N'Nombre';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Código ISO del país (2 letras)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Pais', @level2type = N'COLUMN', @level2name = N'CodigoISO';
GO

-- Tabla de Canales de Venta (Catálogo)
CREATE TABLE sales_ms.Canal (
    CanalId TINYINT PRIMARY KEY,
    Nombre NVARCHAR(20) NOT NULL UNIQUE,
    Descripcion NVARCHAR(150)
);

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla catálogo de canales de venta', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Canal';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único del canal (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Canal', @level2type = N'COLUMN', @level2name = N'CanalId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Nombre del canal de venta', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Canal', @level2type = N'COLUMN', @level2name = N'Nombre';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Descripción del canal de venta', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Canal', @level2type = N'COLUMN', @level2name = N'Descripcion';
GO

-- Tabla de Categorías de Productos (Catálogo)
CREATE TABLE sales_ms.Categoria (
    CategoriaId INT IDENTITY PRIMARY KEY,
    Nombre NVARCHAR(80) NOT NULL UNIQUE,
    Descripcion NVARCHAR(255)
);

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla catálogo de categorías de productos', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Categoria';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único de la categoría (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Categoria', @level2type = N'COLUMN', @level2name = N'CategoriaId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Nombre de la categoría', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Categoria', @level2type = N'COLUMN', @level2name = N'Nombre';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Descripción de la categoría', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Categoria', @level2type = N'COLUMN', @level2name = N'Descripcion';
GO

-- Tabla de Monedas (Catálogo)
CREATE TABLE sales_ms.Moneda (
    MonedaId CHAR(3) PRIMARY KEY,
    Nombre NVARCHAR(50) NOT NULL,
    Simbolo NVARCHAR(5)
);

EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla catálogo de monedas', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Moneda';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Código de la moneda (PK) - ISO 4217', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Moneda', @level2type = N'COLUMN', @level2name = N'MonedaId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Nombre de la moneda', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Moneda', @level2type = N'COLUMN', @level2name = N'Nombre';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Símbolo de la moneda', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Moneda', @level2type = N'COLUMN', @level2name = N'Simbolo';
GO

-- ========= TABLAS PRINCIPALES (Normalización 2FN - Dependencia de la Clave Primaria) =========

-- Tabla de Clientes (Normalizada)
CREATE TABLE sales_ms.Cliente (
    ClienteId INT IDENTITY PRIMARY KEY,
    Nombre NVARCHAR(120) NOT NULL,
    Email NVARCHAR(150) UNIQUE,
    GeneroId TINYINT FOREIGN KEY REFERENCES sales_ms.Genero(GeneroId),
    PaisId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Pais(PaisId),
    FechaRegistro DATE NOT NULL DEFAULT (GETDATE())
);

-- Comentarios de la tabla Cliente
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla que almacena la información de los clientes', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Cliente';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único del cliente (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Cliente', @level2type = N'COLUMN', @level2name = N'ClienteId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Nombre completo del cliente', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Cliente', @level2type = N'COLUMN', @level2name = N'Nombre';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Correo electrónico único del cliente', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Cliente', @level2type = N'COLUMN', @level2name = N'Email';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador del género del cliente (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Cliente', @level2type = N'COLUMN', @level2name = N'GeneroId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador del país de residencia (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Cliente', @level2type = N'COLUMN', @level2name = N'PaisId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Fecha de registro del cliente en el sistema', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Cliente', @level2type = N'COLUMN', @level2name = N'FechaRegistro';
GO

-- Tabla de Productos (Normalizada)
CREATE TABLE sales_ms.Producto (
    ProductoId INT IDENTITY PRIMARY KEY,
    SKU NVARCHAR(40) UNIQUE NOT NULL,
    Nombre NVARCHAR(150) NOT NULL,
    CategoriaId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Categoria(CategoriaId)
);

-- Comentarios de la tabla Producto
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla que almacena la información de los productos disponibles', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Producto';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único del producto (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Producto', @level2type = N'COLUMN', @level2name = N'ProductoId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Código SKU único del producto (Stock Keeping Unit)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Producto', @level2type = N'COLUMN', @level2name = N'SKU';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Nombre o descripción del producto', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Producto', @level2type = N'COLUMN', @level2name = N'Nombre';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador de la categoría del producto (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Producto', @level2type = N'COLUMN', @level2name = N'CategoriaId';
GO

-- ========= TABLAS TRANSACCIONALES (Normalización 3FN - Sin Dependencia Transitiva) =========

-- Tabla de Órdenes
CREATE TABLE sales_ms.Orden (
    OrdenId INT IDENTITY PRIMARY KEY,
    ClienteId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Cliente(ClienteId),
    Fecha DATETIME2 NOT NULL DEFAULT (SYSDATETIME()),
    CanalId TINYINT NOT NULL FOREIGN KEY REFERENCES sales_ms.Canal(CanalId),
    MonedaId CHAR(3) NOT NULL DEFAULT 'USD' FOREIGN KEY REFERENCES sales_ms.Moneda(MonedaId),
    Total DECIMAL(18,2) NOT NULL,
    Estado NVARCHAR(20) NOT NULL DEFAULT 'PENDIENTE' CHECK (Estado IN ('PENDIENTE', 'CONFIRMADA', 'ENVIADA', 'ENTREGADA', 'CANCELADA'))
);

-- Comentarios de la tabla Orden
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla que registra las órdenes de compra realizadas por los clientes', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único de la orden (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden', @level2type = N'COLUMN', @level2name = N'OrdenId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador del cliente que realizó la orden (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden', @level2type = N'COLUMN', @level2name = N'ClienteId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Fecha y hora en que se realizó la orden', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden', @level2type = N'COLUMN', @level2name = N'Fecha';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador del canal de venta de la orden (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden', @level2type = N'COLUMN', @level2name = N'CanalId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador de la moneda en la que se registra la orden (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden', @level2type = N'COLUMN', @level2name = N'MonedaId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Monto total de la orden', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden', @level2type = N'COLUMN', @level2name = N'Total';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Estado actual de la orden', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'Orden', @level2type = N'COLUMN', @level2name = N'Estado';
GO

-- Tabla de Detalle de Órdenes (BCNF - Sin anomalías de actualización)
CREATE TABLE sales_ms.OrdenDetalle (
    OrdenDetalleId INT IDENTITY PRIMARY KEY,
    OrdenId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Orden(OrdenId),
    ProductoId INT NOT NULL FOREIGN KEY REFERENCES sales_ms.Producto(ProductoId), 
    Cantidad INT NOT NULL CHECK (Cantidad > 0),
    PrecioUnitario DECIMAL(18,2) NOT NULL CHECK (PrecioUnitario > 0),
    DescuentoPct DECIMAL(5,2) NULL CHECK (DescuentoPct >= 0 AND DescuentoPct <= 100),
    CONSTRAINT UQ_Orden_Producto UNIQUE (OrdenId, ProductoId)
);

-- Comentarios de la tabla OrdenDetalle
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Tabla que almacena los detalles de línea de cada orden (productos incluidos)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'OrdenDetalle';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador único del detalle de orden (PK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'OrdenDetalle', @level2type = N'COLUMN', @level2name = N'OrdenDetalleId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador de la orden a la que pertenece este detalle (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'OrdenDetalle', @level2type = N'COLUMN', @level2name = N'OrdenId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Identificador del producto incluido en la orden (FK)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'OrdenDetalle', @level2type = N'COLUMN', @level2name = N'ProductoId';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Cantidad de unidades del producto en esta línea de orden', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'OrdenDetalle', @level2type = N'COLUMN', @level2name = N'Cantidad';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Precio unitario del producto en el momento de la orden', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'OrdenDetalle', @level2type = N'COLUMN', @level2name = N'PrecioUnitario';
EXEC sp_addextendedproperty @name = N'MS_Description', @value = N'Porcentaje de descuento aplicado a esta línea de orden (0-100, opcional)', @level0type = N'SCHEMA', @level0name = N'sales_ms', @level1type = N'TABLE', @level1name = N'OrdenDetalle', @level2type = N'COLUMN', @level2name = N'DescuentoPct';
GO

-- ========= ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS =========
CREATE INDEX IX_Cliente_PaisId ON sales_ms.Cliente (PaisId);
CREATE INDEX IX_Cliente_GeneroId ON sales_ms.Cliente (GeneroId);
CREATE INDEX IX_Cliente_Email ON sales_ms.Cliente (Email);
GO

CREATE INDEX IX_Producto_CategoriaId ON sales_ms.Producto (CategoriaId);
CREATE INDEX IX_Producto_SKU ON sales_ms.Producto (SKU);
GO

CREATE INDEX IX_Orden_ClienteId ON sales_ms.Orden (ClienteId);
CREATE INDEX IX_Orden_Fecha ON sales_ms.Orden (Fecha);
CREATE INDEX IX_Orden_CanalId ON sales_ms.Orden (CanalId);
CREATE INDEX IX_Orden_Estado ON sales_ms.Orden (Estado);
GO

CREATE INDEX IX_OrdenDetalle_OrdenId ON sales_ms.OrdenDetalle (OrdenId);
CREATE INDEX IX_OrdenDetalle_ProductoId ON sales_ms.OrdenDetalle (ProductoId);
GO
