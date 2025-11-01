-- ===========================================
-- Funcion: fn_crear_orden
-- Crea una orden y su detalle automáticamente
-- Calcula el total = cantidad * precio_unit
-- ===========================================
create or replace function public.fn_crear_orden(
    p_cliente_id uuid,
    p_producto_id uuid,
    p_fecha timestamp with time zone,
    p_canal text,
    p_moneda char(3),
    p_cantidad integer,
    p_precio_unit numeric(18,2)
)
returns uuid
language plpgsql
as $$
declare
    v_orden_id uuid;
    v_total numeric(18,2);
begin
    -- Validations
    if p_canal not in ('WEB', 'APP', 'PARTNER') then
        raise exception 'Invalid channel: %. Must be WEB, APP, or PARTNER.', p_canal;
    end if;

    if p_cantidad <= 0 then
        raise exception 'Quantity must be > 0. Received: %', p_cantidad;
    end if;

    v_total := p_cantidad * p_precio_unit;

    -- Insert into orden
    insert into public.orden (
        cliente_id, fecha, canal, moneda, total
    )
    values (
        p_cliente_id, coalesce(p_fecha, now()), p_canal, p_moneda, v_total
    )
    returning orden_id into v_orden_id;

    -- Insert into detalle
    insert into public.orden_detalle (
        orden_id, producto_id, cantidad, precio_unit
    )
    values (
        v_orden_id, p_producto_id, p_cantidad, p_precio_unit
    );

    -- Return the new order ID
    return v_orden_id;
end;
$$;
