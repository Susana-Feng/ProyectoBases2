/* ================================================================
 Script para crear el esquema en MS SQL Server
 Esquema: dbo (por defecto)
 Heterogeneidades:
 - Género: 'Masculino', 'Femenino'
 - Moneda: Siempre 'USD'
 - SKU: 'SKU oficial'
================================================================
*/

USE DB_SALES;
GO

-- Nota: No eliminamos el esquema 'dbo' ya que es el esquema por defecto del sistema
-- y siempre existe. Solo eliminamos las tablas si existen.

-- ========= TABLA DE CLIENTES =========
CREATE TABLE dbo.Cliente (
    ClienteId INT IDENTITY PRIMARY KEY,
    Nombre NVARCHAR(120) NOT NULL,
    Email NVARCHAR(150) UNIQUE,
    Genero NVARCHAR(12) CHECK (Genero IN ('Masculino', 'Femenino')),
    Pais NVARCHAR(60) NOT NULL,
    FechaRegistro DATE NOT NULL DEFAULT (GETDATE())
);

-- Comentarios para tabla Cliente
EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Tabla que almacena la información de los clientes',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Cliente';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Identificador único del cliente (clave primaria)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Cliente',
    @level2type = N'COLUMN', @level2name = N'ClienteId';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Nombre completo del cliente',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Cliente',
    @level2type = N'COLUMN', @level2name = N'Nombre';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Correo electrónico único del cliente',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Cliente',
    @level2type = N'COLUMN', @level2name = N'Email';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Género del cliente: Masculino o Femenino',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Cliente',
    @level2type = N'COLUMN', @level2name = N'Genero';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'País de residencia del cliente',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Cliente',
    @level2type = N'COLUMN', @level2name = N'Pais';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Fecha de registro del cliente en el sistema (por defecto fecha actual)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Cliente',
    @level2type = N'COLUMN', @level2name = N'FechaRegistro';

GO

-- ========= TABLA DE PRODUCTOS =========
CREATE TABLE dbo.Producto (
    ProductoId INT IDENTITY PRIMARY KEY,
    SKU NVARCHAR(40) UNIQUE NOT NULL,
    Nombre NVARCHAR(150) NOT NULL,
    Categoria NVARCHAR(80) NOT NULL
);

-- Comentarios para tabla Producto
EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Tabla que almacena la información de los productos disponibles',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Producto';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Identificador único del producto (clave primaria)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Producto',
    @level2type = N'COLUMN', @level2name = N'ProductoId';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Código SKU único del producto (Stock Keeping Unit oficial)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Producto',
    @level2type = N'COLUMN', @level2name = N'SKU';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Nombre o descripción del producto',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Producto',
    @level2type = N'COLUMN', @level2name = N'Nombre';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Categoría a la que pertenece el producto',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Producto',
    @level2type = N'COLUMN', @level2name = N'Categoria';

GO

-- ========= TABLA DE ÓRDENES =========
CREATE TABLE dbo.Orden (
    OrdenId INT IDENTITY PRIMARY KEY,
    ClienteId INT NOT NULL FOREIGN KEY REFERENCES dbo.Cliente(ClienteId),
    Fecha DATETIME2 NOT NULL DEFAULT (SYSDATETIME()),
    Canal NVARCHAR(20) NOT NULL CHECK (Canal IN ('WEB', 'TIENDA', 'APP')),
    Moneda CHAR(3) NOT NULL DEFAULT 'USD',
    Total DECIMAL(18,2) NOT NULL
);

-- Comentarios para tabla Orden
EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Tabla que registra las órdenes de compra realizadas por los clientes',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Orden';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Identificador único de la orden (clave primaria)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Orden',
    @level2type = N'COLUMN', @level2name = N'OrdenId';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Identificador del cliente que realizó la orden (clave foránea)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Orden',
    @level2type = N'COLUMN', @level2name = N'ClienteId';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Fecha y hora en que se realizó la orden (por defecto fecha/hora actual)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Orden',
    @level2type = N'COLUMN', @level2name = N'Fecha';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Canal de venta de la orden: WEB, TIENDA o APP',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Orden',
    @level2type = N'COLUMN', @level2name = N'Canal';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Moneda en la que se registra la orden (por defecto USD)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Orden',
    @level2type = N'COLUMN', @level2name = N'Moneda';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Monto total de la orden con 2 decimales',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'Orden',
    @level2type = N'COLUMN', @level2name = N'Total';

GO

-- ========= TABLA DE DETALLE DE ÓRDENES =========
CREATE TABLE dbo.OrdenDetalle (
    OrdenDetalleId INT IDENTITY PRIMARY KEY,
    OrdenId INT NOT NULL FOREIGN KEY REFERENCES dbo.Orden(OrdenId),
    ProductoId INT NOT NULL FOREIGN KEY REFERENCES dbo.Producto(ProductoId),
    Cantidad INT NOT NULL CHECK (Cantidad > 0),
    PrecioUnit DECIMAL(18,2) NOT NULL,
    DescuentoPct DECIMAL(5,2) NULL
);

-- Comentarios para tabla OrdenDetalle
EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Tabla que almacena los detalles de línea de cada orden (productos incluidos)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'OrdenDetalle';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Identificador único del detalle de orden (clave primaria)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'OrdenDetalle',
    @level2type = N'COLUMN', @level2name = N'OrdenDetalleId';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Identificador de la orden a la que pertenece este detalle (clave foránea)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'OrdenDetalle',
    @level2type = N'COLUMN', @level2name = N'OrdenId';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Identificador del producto incluido en la orden (clave foránea)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'OrdenDetalle',
    @level2type = N'COLUMN', @level2name = N'ProductoId';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Cantidad de unidades del producto en esta línea de orden (debe ser mayor a 0)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'OrdenDetalle',
    @level2type = N'COLUMN', @level2name = N'Cantidad';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Precio unitario del producto en el momento de la orden con 2 decimales',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'OrdenDetalle',
    @level2type = N'COLUMN', @level2name = N'PrecioUnit';

EXEC sp_addextendedproperty @name = N'MS_Description',
    @value = N'Porcentaje de descuento aplicado a esta línea de orden (0-100, opcional/nullable)',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'OrdenDetalle',
    @level2type = N'COLUMN', @level2name = N'DescuentoPct';

GO

-- ========= ÍNDICES PARA OPTIMIZACIÓN =========
CREATE INDEX IX_Orden_ClienteId ON dbo.Orden (ClienteId);
CREATE INDEX IX_Orden_Fecha ON dbo.Orden (Fecha);
CREATE INDEX IX_OrdenDetalle_OrdenId ON dbo.OrdenDetalle (OrdenId);
CREATE INDEX IX_OrdenDetalle_ProductoId ON dbo.OrdenDetalle (ProductoId);
GO