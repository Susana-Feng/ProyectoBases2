-- ===========================================
-- Script unificado de Supabase
-- Crea tablas, funciones y vistas necesarias
-- ===========================================
-- Nota: para aplicar schema + datos de ejemplo utiliza scripts/Supabase/init.sql

-- Extensión para UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =======================
-- Limpiar objetos existentes
-- =======================
DROP VIEW IF EXISTS public.orden_completa;

DROP FUNCTION IF EXISTS public.fn_eliminar_orden(uuid);
DROP FUNCTION IF EXISTS public.fn_actualizar_orden_completa(
  uuid,
  uuid,
  text,
  text,
  text,
  jsonb
);
DROP FUNCTION IF EXISTS public.fn_crear_orden(
  uuid,
  text,
  text,
  text,
  jsonb
);

DROP TABLE IF EXISTS orden_detalle CASCADE;
DROP TABLE IF EXISTS orden CASCADE;
DROP TABLE IF EXISTS producto CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;

-- =======================
-- Tablas
-- =======================

CREATE TABLE cliente (
 cliente_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 nombre TEXT NOT NULL,
 email TEXT UNIQUE,
 genero CHAR(1) NOT NULL CHECK (genero IN ('M','F')),
 pais TEXT NOT NULL,
 fecha_registro DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE producto (
 producto_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 sku TEXT UNIQUE,
 nombre TEXT NOT NULL,
 categoria TEXT NOT NULL
);

CREATE TABLE orden (
 orden_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 cliente_id UUID NOT NULL REFERENCES cliente(cliente_id),
 fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 canal TEXT NOT NULL CHECK (canal IN ('WEB','APP','PARTNER')),
 moneda CHAR(3) NOT NULL,
 total NUMERIC(18,2) NOT NULL
);

CREATE TABLE orden_detalle (
 orden_detalle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 orden_id UUID NOT NULL REFERENCES orden(orden_id),
 producto_id UUID NOT NULL REFERENCES producto(producto_id),
 cantidad INT NOT NULL CHECK (cantidad > 0),
 precio_unit NUMERIC(18,2) NOT NULL
);

CREATE INDEX ix_orden_fecha ON orden(fecha);
CREATE INDEX ix_detalle_producto ON orden_detalle(producto_id);

-- =======================
-- Funciones
-- =======================

-- Crear orden
CREATE OR REPLACE FUNCTION fn_crear_orden(
  p_cliente_id UUID,
  p_fecha TEXT,
  p_canal TEXT,
  p_moneda TEXT,
  p_items JSONB
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
  nueva_orden_id UUID;
  item_record JSONB;
  total_calculado NUMERIC := 0;
BEGIN
  nueva_orden_id := gen_random_uuid();

  SELECT SUM((item->>'cantidad')::NUMERIC * (item->>'precio_unitario')::NUMERIC)
  INTO total_calculado
  FROM jsonb_array_elements(p_items) AS item;

  INSERT INTO orden (
    orden_id,
    cliente_id,
    fecha,
    canal,
    moneda,
    total
  ) VALUES (
    nueva_orden_id,
    p_cliente_id,
    p_fecha::TIMESTAMPTZ,
    p_canal,
    p_moneda,
    total_calculado
  );

  FOR item_record IN SELECT * FROM jsonb_array_elements(p_items)
  LOOP
    INSERT INTO orden_detalle (
      orden_id,
      producto_id,
      cantidad,
      precio_unit
    ) VALUES (
      nueva_orden_id,
      (item_record->>'producto_id')::UUID,
      (item_record->>'cantidad')::INTEGER,
      (item_record->>'precio_unitario')::NUMERIC
    );
  END LOOP;

  RETURN json_build_object(
    'status', 'success',
    'message', 'Orden creada correctamente',
    'orden_id', nueva_orden_id
  );
END;
$$;

-- Actualizar orden completa
CREATE OR REPLACE FUNCTION fn_actualizar_orden_completa(
  p_orden_id UUID,
  p_cliente_id UUID,
  p_fecha TEXT,
  p_canal TEXT,
  p_moneda TEXT,
  p_items JSONB
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
  item_record JSONB;
  total_calculado NUMERIC := 0;
BEGIN
  SELECT SUM((item->>'cantidad')::NUMERIC * (item->>'precio_unitario')::NUMERIC)
  INTO total_calculado
  FROM jsonb_array_elements(p_items) AS item;

  UPDATE orden
  SET
    cliente_id = p_cliente_id,
    fecha = p_fecha::TIMESTAMPTZ,
    canal = p_canal,
    moneda = p_moneda,
    total = total_calculado
  WHERE orden_id = p_orden_id;

  DELETE FROM orden_detalle WHERE orden_id = p_orden_id;

  FOR item_record IN SELECT * FROM jsonb_array_elements(p_items)
  LOOP
    INSERT INTO orden_detalle (
      orden_id,
      producto_id,
      cantidad,
      precio_unit
    ) VALUES (
      p_orden_id,
      (item_record->>'producto_id')::UUID,
      (item_record->>'cantidad')::INTEGER,
      (item_record->>'precio_unitario')::NUMERIC
    );
  END LOOP;

  RETURN json_build_object('status', 'success', 'message', 'Orden actualizada correctamente');
END;
$$;

-- Eliminar orden
CREATE OR REPLACE FUNCTION public.fn_eliminar_orden(
  p_orden_id uuid
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
  v_exist boolean;
BEGIN
  SELECT EXISTS(SELECT 1 FROM public.orden WHERE orden_id = p_orden_id)
  INTO v_exist;

  IF NOT v_exist THEN
    RAISE EXCEPTION 'La orden con ID % no existe.', p_orden_id;
  END IF;

  DELETE FROM public.orden_detalle
  WHERE orden_id = p_orden_id;

  DELETE FROM public.orden
  WHERE orden_id = p_orden_id;

  RETURN true;
END;
$$;

-- =======================
-- Vista
-- =======================

CREATE OR REPLACE VIEW public.orden_completa AS
SELECT
    o.orden_id,
    o.fecha,
    o.canal,
    o.moneda,
    o.total,
    d.cantidad,
    d.precio_unit AS precio_unitario,
    p.producto_id,
    c.cliente_id,
    p.nombre AS nombre_producto,
    c.nombre AS nombre_cliente
FROM public.orden o
INNER JOIN public.orden_detalle d ON o.orden_id = d.orden_id
INNER JOIN public.producto p ON p.producto_id = d.producto_id
INNER JOIN public.cliente c ON c.cliente_id = o.cliente_id;
