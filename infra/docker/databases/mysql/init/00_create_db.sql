/* ================================================================
 Script para crear la base de datos en MySQL
 Base de datos: DB_SALES
 Propósito: Crear la BD desde cero con capacidad de reinicialización
================================================================
*/

-- Eliminar la base de datos si existe
DROP DATABASE IF EXISTS DB_SALES;

-- Crear la base de datos
CREATE DATABASE DB_SALES
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE DB_SALES;
