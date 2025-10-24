/* ================================================================
 Script para crear la BD de origen en MS SQL Server
 Base de datos: sales_db
================================================================
*/

-- Eliminar la base de datos si existe
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'sales_db')
BEGIN
    ALTER DATABASE sales_db SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE sales_db;
END
GO

-- Crear la base de datos
CREATE DATABASE sales_db;
GO

-- Usar la base de datos
USE sales_db;
GO
