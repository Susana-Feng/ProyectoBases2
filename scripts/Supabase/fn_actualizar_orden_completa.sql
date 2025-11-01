-- ===========================================
-- Funcion: fn_actualizar_orden_completa
-- Actualiza una orden y su detalles automáticamente
-- Calcula el total = cantidad * precio_unit
-- ===========================================

CREATE OR REPLACE FUNCTION fn_actualizar_orden_completa(
  p_orden_id UUID,
  p_cliente_id UUID,
  p_fecha TEXT,  -- Usar TEXT para flexibilidad
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
  -- Calcular el total
  SELECT SUM((item->>'cantidad')::NUMERIC * (item->>'precio_unitario')::NUMERIC)
  INTO total_calculado
  FROM jsonb_array_elements(p_items) AS item;
  
  -- Actualizar la orden principal
  UPDATE orden 
  SET 
    cliente_id = p_cliente_id,
    fecha = p_fecha::TIMESTAMPTZ,  -- Convertir TEXT a TIMESTAMPTZ
    canal = p_canal,
    moneda = p_moneda,
    total = total_calculado
  WHERE orden_id = p_orden_id;
  
  -- Eliminar items existentes
  DELETE FROM orden_detalle WHERE orden_id = p_orden_id;
  
  -- Insertar nuevos items
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