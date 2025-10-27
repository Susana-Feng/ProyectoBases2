/* ================================================================
 Script para crear el esquema en MySQL
 Base de datos: DB_SALES
 Heterogeneidades:
 - Género: ENUM('M','F', 'X') Default 'M'
 - Moneda: Puede ser 'USD' o 'CRC' unicamente (CHAR(3))
 - Canal: libre (no controlado)
 - Fechas: Almacenadas como VARCHAR
 - Montos: Almacenados como VARCHAR, a veces '1200.50' o '1,200.50'
 - Código Producto: 'codigo_alt' código alterno (no coincide con SKU oficial)
 - OrdenDetalle: NO tiene restricción UNIQUE en (orden_id, producto_id)
   (puede haber duplicados del mismo producto en una orden)
================================================================
*/

USE DB_SALES;

-- Tabla de Clientes
CREATE TABLE Cliente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL COMMENT 'Nombre completo del cliente',
    correo VARCHAR(150) COMMENT 'Correo electrónico del cliente (sin restricción UNIQUE)',
    genero ENUM('M', 'F', 'X') DEFAULT 'M' COMMENT 'Género del cliente (M=Masculino, F=Femenino, X=Otro). Default M',
    pais VARCHAR(60) NOT NULL COMMENT 'País de residencia del cliente',
    created_at VARCHAR(10) NOT NULL COMMENT 'Fecha de registro en formato VARCHAR (YYYY-MM-DD)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla que almacena la información de los clientes';

-- Tabla de Productos
CREATE TABLE Producto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_alt VARCHAR(64) UNIQUE NOT NULL COMMENT 'Código alternativo del producto (NO es el SKU oficial)',
    nombre VARCHAR(150) NOT NULL COMMENT 'Nombre o descripción del producto',
    categoria VARCHAR(80) NOT NULL COMMENT 'Categoría del producto'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla que almacena la información de los productos disponibles';

-- Tabla de Órdenes
CREATE TABLE Orden (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL COMMENT 'Identificador del cliente (FK)',
    fecha VARCHAR(19) NOT NULL COMMENT 'Fecha y hora de la orden en formato VARCHAR (YYYY-MM-DD HH:MM:SS)',
    canal VARCHAR(20) NOT NULL COMMENT 'Canal de venta (libre, no controlado - valores como WEB, TIENDA, APP, etc.)',
    moneda CHAR(3) NOT NULL COMMENT 'Moneda de la orden (puede ser USD o CRC)',
    total VARCHAR(20) NOT NULL COMMENT 'Monto total de la orden en VARCHAR (puede tener formato 1200.50 o 1,200.50)',
    FOREIGN KEY (cliente_id) REFERENCES Cliente(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla que registra las órdenes de compra realizadas por los clientes';

-- Tabla de Detalle de Órdenes
CREATE TABLE OrdenDetalle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orden_id INT NOT NULL COMMENT 'Identificador de la orden (FK)',
    producto_id INT NOT NULL COMMENT 'Identificador del producto (FK)',
    cantidad INT NOT NULL COMMENT 'Cantidad de unidades del producto',
    precio_unit VARCHAR(20) NOT NULL COMMENT 'Precio unitario en VARCHAR (puede tener formato 100.50 o 100,50)',
    FOREIGN KEY (orden_id) REFERENCES Orden(id),
    FOREIGN KEY (producto_id) REFERENCES Producto(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Tabla que almacena los detalles de línea de cada orden (productos incluidos)';

-- Índices según especificación
CREATE INDEX IX_Orden_cliente ON Orden(cliente_id);
CREATE INDEX IX_Detalle_producto ON OrdenDetalle(producto_id);
