-- ===========================================
-- Funcion: fn_actualizar_orden
-- Actualiza una orden y su detalle automáticamente
-- Calcula el total = cantidad * precio_unit
-- ===========================================

create or replace function public.fn_actualizar_orden(
    p_orden_id uuid,
    p_cliente_id uuid,
    p_producto_id uuid,
    p_fecha timestamptz,
    p_canal text,
    p_moneda char(3),
    p_cantidad integer,
    p_precio_unit numeric(18,2)
)
returns json
language plpgsql
as $$
declare
    v_exist_orden boolean;
    v_exist_cliente boolean;
    v_exist_producto boolean;
    v_total numeric(18,2);
begin
    -- Verificar que la orden exista
    select exists(select 1 from public.orden where orden_id = p_orden_id)
    into v_exist_orden;
    if not v_exist_orden then
        raise exception 'La orden con ID % no existe.', p_orden_id;
    end if;

    -- Verificar cliente válido
    select exists(select 1 from public.cliente where cliente_id = p_cliente_id)
    into v_exist_cliente;
    if not v_exist_cliente then
        raise exception 'El cliente con ID % no existe.', p_cliente_id;
    end if;

    -- Verificar producto válido
    select exists(select 1 from public.producto where producto_id = p_producto_id)
    into v_exist_producto;
    if not v_exist_producto then
        raise exception 'El producto con ID % no existe.', p_producto_id;
    end if;

    -- Validar canal permitido
    if p_canal not in ('WEB', 'APP', 'PARTNER') then
        raise exception 'Canal inválido: %. Debe ser WEB, APP o PARTNER.', p_canal;
    end if;

    -- Validar cantidad
    if p_cantidad <= 0 then
        raise exception 'La cantidad debe ser mayor que 0. Valor recibido: %', p_cantidad;
    end if;

    -- Calcular total automáticamente
    v_total := p_cantidad * p_precio_unit;

    -- Actualizar encabezado de orden (ahora sí incluye la fecha)
    update public.orden
    set
        cliente_id = p_cliente_id,
        fecha = p_fecha,
        canal = p_canal,
        moneda = p_moneda,
        total = v_total
    where orden_id = p_orden_id;

    -- Actualizar detalle
    update public.orden_detalle
    set
        producto_id = p_producto_id,
        cantidad = p_cantidad,
        precio_unit = p_precio_unit
    where orden_id = p_orden_id;

    --  Retornar información de la orden actualizada
    return json_build_object(
        'orden_id', p_orden_id,
        'cliente_id', p_cliente_id,
        'producto_id', p_producto_id,
        'nueva_fecha', p_fecha,
        'nuevo_total', v_total,
        'mensaje', 'Orden actualizada correctamente'
    );
end;
$$;
