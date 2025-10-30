/* ================================================================
 Script para crear la BD de origen en MS SQL Server
 Base de datos: DB_SALES
================================================================
*/

-- Eliminar la base de datos si existe
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'DB_SALES')
BEGIN
    ALTER DATABASE DB_SALES SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE DB_SALES;
END
GO

-- Crear la base de datos
CREATE DATABASE DB_SALES;
GO

-- Usar la base de datos
USE DB_SALES;
GO
