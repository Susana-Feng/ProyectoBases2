// ============================
// LIMPIEZA DE BASE DE DATOS
// ============================

// Eliminar relaciones y nodos existentes
MATCH (n)
DETACH DELETE n;

// Eliminar constraints si existen
DROP CONSTRAINT cliente_id IF EXISTS;
DROP CONSTRAINT producto_id IF EXISTS;

// Eliminar índices si existen
DROP INDEX orden_fecha IF EXISTS;

// ============================
// CREACIÓN DE CONSTRAINTS E ÍNDICES
// ============================

CREATE CONSTRAINT cliente_id IF NOT EXISTS
FOR (c:Cliente)
REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT producto_id IF NOT EXISTS
FOR (p:Producto)
REQUIRE p.id IS UNIQUE;

CREATE INDEX orden_fecha IF NOT EXISTS
FOR (o:Orden)
ON (o.fecha);