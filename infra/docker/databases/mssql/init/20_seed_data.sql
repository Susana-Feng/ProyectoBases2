/* ================================================================
 Script de datos semilla para MS SQL Server
 Esquema: sales_ms
 Base de datos: sales_db
 Descripción: Inserta datos iniciales para pruebas y desarrollo
 Heterogeneidades:
 - Género: 'Masculino', 'Femenino'
 - Moneda: Siempre 'USD'
 - SKU: Código oficial de producto
================================================================
*/

USE sales_db;
GO

-- Insertar Clientes
INSERT INTO dbo.Cliente (Nombre, Email, Genero, Pais, FechaRegistro) VALUES
('Juan Pérez López', 'juan.perez@example.com', 'Masculino', 'Colombia', '2025-01-15'),
('María García Rodríguez', 'maria.garcia@example.com', 'Femenino', 'Colombia', '2025-01-20'),
('Carlos López Martínez', 'carlos.lopez@example.com', 'Masculino', 'México', '2025-02-05'),
('Ana Martínez Sánchez', 'ana.martinez@example.com', 'Femenino', 'México', '2025-02-10'),
('Roberto Rodríguez García', 'roberto.rodriguez@example.com', 'Masculino', 'Argentina', '2025-02-15'),
('Sofía González López', 'sofia.gonzalez@example.com', 'Femenino', 'Brasil', '2025-02-20'),
('Diego Fernández Torres', 'diego.fernandez@example.com', 'Masculino', 'Chile', '2025-03-01'),
('Gabriela Sánchez Ruiz', 'gabriela.sanchez@example.com', 'Femenino', 'Perú', '2025-03-05');

GO

-- Insertar Productos
INSERT INTO dbo.Producto (SKU, Nombre, Categoria) VALUES
('SKU-ELEC-001', 'Laptop Dell XPS 13', 'Electrónica'),
('SKU-ELEC-002', 'Monitor Samsung 24"', 'Electrónica'),
('SKU-ELEC-003', 'Mouse Logitech MX Master 3', 'Electrónica'),
('SKU-ELEC-004', 'Teclado Mecánico RGB', 'Electrónica'),
('SKU-ROPA-001', 'Camiseta Básica Hombre L', 'Ropa y Accesorios'),
('SKU-ROPA-002', 'Jeans Azul Clásico 32', 'Ropa y Accesorios'),
('SKU-ROPA-003', 'Zapatos Deportivos Nike', 'Ropa y Accesorios'),
('SKU-HOGAR-001', 'Almohada Memoria de Espuma', 'Hogar'),
('SKU-HOGAR-002', 'Sábanas Algodón 100%', 'Hogar'),
('SKU-HOGAR-003', 'Mantel Decorativo Premium', 'Hogar'),
('SKU-LIBRO-001', 'Cien Años de Soledad - García Márquez', 'Libros'),
('SKU-LIBRO-002', 'Don Quijote - Miguel de Cervantes', 'Libros'),
('SKU-LIBRO-003', 'Ficciones - Jorge Luis Borges', 'Libros'),
('SKU-DEPO-001', 'Mancuernas Ajustables Set', 'Deportes'),
('SKU-DEPO-002', 'Tapete Yoga Premium', 'Deportes'),
('SKU-BELLE-001', 'Protector Solar SPF 50', 'Belleza'),
('SKU-BELLE-002', 'Crema Facial Hidratante', 'Belleza'),
('SKU-BELLE-003', 'Serum Vitamina C', 'Belleza');

GO

-- Insertar Órdenes
INSERT INTO dbo.Orden (ClienteId, Fecha, Canal, Moneda, Total) VALUES
(1, '2025-03-10 10:30:00', 'WEB', 'USD', 1299.99),
(2, '2025-03-11 14:15:00', 'WEB', 'USD', 850.00),
(3, '2025-03-12 09:45:00', 'TIENDA', 'USD', 1599.50),
(4, '2025-03-13 16:20:00', 'APP', 'USD', 89.99),
(5, '2025-03-14 11:00:00', 'WEB', 'USD', 450.00),
(1, '2025-03-15 13:30:00', 'TIENDA', 'USD', 259.98),
(6, '2025-03-16 15:45:00', 'APP', 'USD', 899.90),
(7, '2025-03-17 10:15:00', 'WEB', 'USD', 199.99),
(8, '2025-03-18 12:00:00', 'WEB', 'USD', 599.95);

GO

-- Insertar Detalles de Órdenes
INSERT INTO dbo.OrdenDetalle (OrdenId, ProductoId, Cantidad, PrecioUnit, DescuentoPct) VALUES
-- Orden 1: Juan compra Laptop y Monitor
(1, 1, 1, 999.99, NULL),
(1, 2, 1, 299.99, NULL),
-- Orden 2: María compra Camiseta y Jeans
(2, 5, 2, 25.00, 10.00),
(2, 6, 1, 120.00, NULL),
-- Orden 3: Carlos compra Zapatos
(3, 7, 1, 1599.50, NULL),
-- Orden 4: Ana compra Mouse y Tapete Yoga
(4, 3, 1, 49.99, NULL),
(4, 15, 1, 39.99, NULL),
-- Orden 5: Roberto compra Almohada y Sábanas
(5, 8, 1, 150.00, NULL),
(5, 9, 2, 150.00, NULL),
-- Orden 6: Juan compra Libros
(6, 11, 1, 29.99, 5.00),
(6, 12, 1, 29.99, NULL),
-- Orden 7: Sofía compra Productos de Belleza
(7, 16, 1, 49.99, NULL),
(7, 17, 1, 54.99, NULL),
-- Orden 8: Diego compra Mancuernas
(8, 14, 1, 199.99, NULL),
-- Orden 9: Gabriela compra Crema Facial
(9, 17, 1, 59.95, NULL);

GO

-- Mensaje de confirmación
PRINT '✓ Datos semilla insertados correctamente en el esquema dbo';
PRINT '  - 8 Clientes (Masculino/Femenino)';
PRINT '  - 18 Productos con SKU oficial';
PRINT '  - 9 Órdenes en USD';
PRINT '  - 15 Líneas de detalle';
GO
