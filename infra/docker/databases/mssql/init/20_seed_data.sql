/* ================================================================
 Script de datos semilla para MS SQL Server
 Base de datos: sales_db
 Esquema: sales_ms
 Descripción: Inserta datos iniciales para pruebas y desarrollo
================================================================
*/

USE sales_db;
GO

-- ========= TABLAS CATÁLOGOS - Inserción de datos =========

-- Insertar Géneros
INSERT INTO sales_ms.Genero (GeneroId, Nombre, Descripcion)
VALUES 
    (1, N'Masculino', N'Cliente de género masculino'),
    (2, N'Femenino', N'Cliente de género femenino');
GO

-- Insertar Países
INSERT INTO sales_ms.Pais (Nombre, CodigoISO)
VALUES 
    (N'Colombia', N'CO'),
    (N'México', N'MX'),
    (N'Argentina', N'AR'),
    (N'Brasil', N'BR'),
    (N'Chile', N'CL'),
    (N'Perú', N'PE'),
    (N'España', N'ES'),
    (N'Estados Unidos', N'US');
GO

-- Insertar Canales de Venta
INSERT INTO sales_ms.Canal (CanalId, Nombre, Descripcion)
VALUES 
    (1, N'WEB', N'Ventas a través del sitio web'),
    (2, N'TIENDA', N'Ventas en tienda física'),
    (3, N'APP', N'Ventas a través de la aplicación móvil');
GO

-- Insertar Categorías de Productos
INSERT INTO sales_ms.Categoria (Nombre, Descripcion)
VALUES 
    (N'Electrónica', N'Dispositivos electrónicos y componentes'),
    (N'Ropa y Accesorios', N'Prendas de vestir y accesorios'),
    (N'Hogar', N'Artículos para el hogar'),
    (N'Libros', N'Libros y material de lectura'),
    (N'Deportes', N'Equipamiento y accesorios deportivos'),
    (N'Belleza', N'Productos de belleza y cuidado personal');
GO

-- Insertar Monedas
INSERT INTO sales_ms.Moneda (MonedaId, Nombre, Simbolo)
VALUES 
    (N'USD', N'Dólar Estadounidense', N'$'),
    (N'COP', N'Peso Colombiano', N'$'),
    (N'MXN', N'Peso Mexicano', N'$'),
    (N'ARS', N'Peso Argentino', N'$'),
    (N'BRL', N'Real Brasileño', N'R$'),
    (N'CLP', N'Peso Chileno', N'$'),
    (N'PEN', N'Sol Peruano', N'S/'),
    (N'EUR', N'Euro', N'€');
GO

-- ========= TABLAS PRINCIPALES =========

-- Insertar Clientes
INSERT INTO sales_ms.Cliente (Nombre, Email, GeneroId, PaisId, FechaRegistro)
VALUES 
    (N'Juan Pérez', N'juan.perez@example.com', 1, 1, '2025-01-15'),
    (N'María García', N'maria.garcia@example.com', 2, 1, '2025-01-20'),
    (N'Carlos López', N'carlos.lopez@example.com', 1, 2, '2025-02-05'),
    (N'Ana Martínez', N'ana.martinez@example.com', 2, 2, '2025-02-10'),
    (N'Roberto Rodríguez', N'roberto.rodriguez@example.com', 1, 3, '2025-02-15'),
    (N'Sofía González', N'sofia.gonzalez@example.com', 2, 4, '2025-02-20'),
    (N'Diego Fernández', N'diego.fernandez@example.com', 1, 5, '2025-03-01'),
    (N'Gabriela Sánchez', N'gabriela.sanchez@example.com', 2, 6, '2025-03-05');
GO

-- Insertar Productos
INSERT INTO sales_ms.Producto (SKU, Nombre, CategoriaId)
VALUES 
    (N'ELEC-001', N'Laptop Dell XPS 13', 1),
    (N'ELEC-002', N'Monitor Samsung 24"', 1),
    (N'ELEC-003', N'Mouse Logitech MX Master 3', 1),
    (N'ROPA-001', N'Camiseta Básica Hombre', 2),
    (N'ROPA-002', N'Jeans Azul Clásico', 2),
    (N'ROPA-003', N'Zapatos Deportivos Nike', 2),
    (N'HOGAR-001', N'Almohada Memoria de Espuma', 3),
    (N'HOGAR-002', N'Sábanas Algodón 100%', 3),
    (N'LIBRO-001', N'Cien Años de Soledad - García Márquez', 4),
    (N'LIBRO-002', N'Don Quijote - Miguel de Cervantes', 4),
    (N'DEPO-001', N'Mancuernas Ajustables Set', 5),
    (N'DEPO-002', N'Tapete Yoga Premium', 5),
    (N'BELLE-001', N'Protector Solar SPF 50', 6),
    (N'BELLE-002', N'Crema Facial Hidratante', 6);
GO

-- ========= TABLAS TRANSACCIONALES =========

-- Insertar Órdenes
INSERT INTO sales_ms.Orden (ClienteId, Fecha, CanalId, MonedaId, Total, Estado)
VALUES 
    (1, '2025-03-10 10:30:00', 1, 'USD', 1299.99, 'ENTREGADA'),
    (2, '2025-03-11 14:15:00', 1, 'COP', 4500000.00, 'CONFIRMADA'),
    (3, '2025-03-12 09:45:00', 2, 'MXN', 15999.50, 'ENTREGADA'),
    (4, '2025-03-13 16:20:00', 3, 'USD', 89.99, 'ENVIADA'),
    (5, '2025-03-14 11:00:00', 1, 'ARS', 45000.00, 'PENDIENTE'),
    (1, '2025-03-15 13:30:00', 2, 'USD', 259.98, 'ENTREGADA'),
    (6, '2025-03-16 15:45:00', 3, 'BRL', 899.90, 'CONFIRMADA'),
    (7, '2025-03-17 10:15:00', 1, 'CLP', 399990.00, 'ENTREGADA'),
    (8, '2025-03-18 12:00:00', 1, 'PEN', 599.95, 'CONFIRMADA');
GO

-- Insertar Detalles de Órdenes
-- Orden 1: Juan compra Laptop y Monitor
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (1, 1, 1, 999.99, 0.00),
    (1, 2, 1, 299.99, 0.00);
GO

-- Orden 2: María compra Camiseta y Jeans
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (2, 4, 2, 25000.00, 5.00),
    (2, 5, 1, 120000.00, 0.00);
GO

-- Orden 3: Carlos compra Zapatos
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (3, 6, 1, 15999.50, 0.00);
GO

-- Orden 4: Ana compra Mouse y Tapete Yoga
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (4, 3, 1, 49.99, 10.00),
    (4, 12, 1, 39.99, 0.00);
GO

-- Orden 5: Roberto compra Almohada y Sábanas
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (5, 7, 1, 15000.00, 0.00),
    (5, 8, 2, 15000.00, 0.00);
GO

-- Orden 6: Juan compra Libros (orden adicional)
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (6, 9, 1, 29.99, 15.00),
    (6, 10, 1, 29.99, 0.00);
GO

-- Orden 7: Sofía compra Productos de Belleza
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (7, 13, 1, 49.99, 0.00),
    (7, 14, 1, 54.99, 8.00);
GO

-- Orden 8: Diego compra Mancuernas
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (8, 11, 1, 199990.00, 0.00);
GO

-- Orden 9: Gabriela compra Crema Facial
INSERT INTO sales_ms.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnitario, DescuentoPct)
VALUES 
    (9, 14, 1, 59.99, 0.00);
GO

PRINT N'✓ Datos semilla insertados exitosamente en todas las tablas.';
PRINT N'✓ Total de clientes: 8';
PRINT N'✓ Total de productos: 14';
PRINT N'✓ Total de órdenes: 9';
PRINT N'✓ Total de detalles de órdenes: 13';
GO
