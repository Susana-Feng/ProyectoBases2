/* ================================================================
 Script de datos semilla para MySQL
 Base de datos: sales_mysql
 Descripción: Inserta datos iniciales para pruebas y desarrollo
 Heterogeneidades:
 - Género: ENUM('M','F', 'X')
 - Moneda: ENUM('USD', 'CRC')
 - Fechas: VARCHAR (YYYY-MM-DD HH:MM:SS)
 - Montos: VARCHAR (pueden tener formato 1200.50 o 1,200.50)
 - Código Producto: código_alt (NO es SKU oficial)
================================================================
*/

USE sales_mysql;

-- Insertar Clientes
INSERT INTO Cliente (nombre, correo, genero, pais, created_at) VALUES
('Juan Pérez', 'juan.perez@example.com', 'M', 'Colombia', '2025-01-15'),
('María García', 'maria.garcia@example.com', 'F', 'Colombia', '2025-01-20'),
('Carlos López', 'carlos.lopez@example.com', 'M', 'México', '2025-02-05'),
('Ana Martínez', 'ana.martinez@example.com', 'F', 'México', '2025-02-10'),
('Roberto Rodríguez', 'roberto.rodriguez@example.com', 'M', 'Argentina', '2025-02-15'),
('Sofía González', 'sofia.gonzalez@example.com', 'F', 'Brasil', '2025-02-20'),
('Diego Fernández', 'diego.fernandez@example.com', 'M', 'Chile', '2025-03-01'),
('Gabriela Sánchez', 'gabriela.sanchez@example.com', 'F', 'Perú', '2025-03-05');

-- Insertar Productos
INSERT INTO Producto (codigo_alt, nombre, categoria) VALUES
('ALT-ELEC-001', 'Laptop Dell XPS 13', 'Electrónica'),
('ALT-ELEC-002', 'Monitor Samsung 24"', 'Electrónica'),
('ALT-ELEC-003', 'Mouse Logitech MX Master 3', 'Electrónica'),
('ALT-ROPA-001', 'Camiseta Básica Hombre', 'Ropa y Accesorios'),
('ALT-ROPA-002', 'Jeans Azul Clásico', 'Ropa y Accesorios'),
('ALT-ROPA-003', 'Zapatos Deportivos Nike', 'Ropa y Accesorios'),
('ALT-HOGAR-001', 'Almohada Memoria de Espuma', 'Hogar'),
('ALT-HOGAR-002', 'Sábanas Algodón 100%', 'Hogar'),
('ALT-LIBRO-001', 'Cien Años de Soledad - García Márquez', 'Libros'),
('ALT-LIBRO-002', 'Don Quijote - Miguel de Cervantes', 'Libros'),
('ALT-DEPO-001', 'Mancuernas Ajustables Set', 'Deportes'),
('ALT-DEPO-002', 'Tapete Yoga Premium', 'Deportes'),
('ALT-BELLE-001', 'Protector Solar SPF 50', 'Belleza'),
('ALT-BELLE-002', 'Crema Facial Hidratante', 'Belleza');

-- Insertar Órdenes
INSERT INTO Orden (cliente_id, fecha, canal, moneda, total) VALUES
(1, '2025-03-10 10:30:00', 'WEB', 'USD', '1299.99'),
(2, '2025-03-11 14:15:00', 'WEB', 'CRC', '850,000.00'),
(3, '2025-03-12 09:45:00', 'TIENDA', 'USD', '15999.50'),
(4, '2025-03-13 16:20:00', 'APP', 'USD', '89.99'),
(5, '2025-03-14 11:00:00', 'WEB', 'CRC', '45,000.00'),
(1, '2025-03-15 13:30:00', 'TIENDA', 'USD', '259.98'),
(6, '2025-03-16 15:45:00', 'APP', 'CRC', '899.90'),
(7, '2025-03-17 10:15:00', 'WEB', 'USD', '199.99'),
(8, '2025-03-18 12:00:00', 'WEB', 'CRC', '599.95');

-- Insertar Detalles de Órdenes
INSERT INTO OrdenDetalle (orden_id, producto_id, cantidad, precio_unit) VALUES
-- Orden 1: Juan compra Laptop y Monitor
(1, 1, 1, '999.99'),
(1, 2, 1, '299.99'),
-- Orden 2: María compra Camiseta y Jeans
(2, 4, 2, '25,000.00'),
(2, 5, 1, '120,000.00'),
-- Orden 3: Carlos compra Zapatos
(3, 6, 1, '15999.50'),
-- Orden 4: Ana compra Mouse y Tapete Yoga
(4, 3, 1, '49.99'),
(4, 12, 1, '39.99'),
-- Orden 5: Roberto compra Almohada y Sábanas
(5, 7, 1, '15,000.00'),
(5, 8, 2, '15,000.00'),
-- Orden 6: Juan compra Libros
(6, 9, 1, '29.99'),
(6, 10, 1, '29.99'),
-- Orden 7: Sofía compra Productos de Belleza
(7, 13, 1, '49.99'),
(7, 14, 1, '54.99'),
-- Orden 8: Diego compra Mancuernas
(8, 11, 1, '199.99'),
-- Orden 9: Gabriela compra Crema Facial
(9, 14, 1, '59.95');
