-- ===========================================
-- Stored Procedure: sp_crear_orden
-- Crea una orden y su detalle automáticamente
-- Calcula el total = cantidad * precio_unit
-- ===========================================
create or replace procedure public.sp_crear_orden(
    p_cliente_id uuid,
    p_producto_id uuid,
    p_fecha timestamp with time zone,
    p_canal text,
    p_moneda char(3),
    p_cantidad integer,
    p_precio_unit numeric(18,2)
)
language plpgsql
as $$
declare
    v_orden_id uuid;
    v_total numeric(18,2);
begin
    -- Validar canal permitido
    if p_canal not in ('WEB', 'APP', 'PARTNER') then
        raise exception 'Canal inválido: %. Debe ser WEB, APP o PARTNER.', p_canal;
    end if;

    -- Validar cantidad positiva
    if p_cantidad <= 0 then
        raise exception 'La cantidad debe ser mayor que 0. Valor recibido: %', p_cantidad;
    end if;

    -- Calcular total automáticamente
    v_total := p_cantidad * p_precio_unit;

    -- Insertar orden principal
    insert into public.orden (
        cliente_id,
        fecha,
        canal,
        moneda,
        total
    )
    values (
        p_cliente_id,
        coalesce(p_fecha, now()),
        p_canal,
        p_moneda,
        v_total
    )
    returning orden_id into v_orden_id;

    -- Insertar detalle de la orden
    insert into public.orden_detalle (
        orden_id,
        producto_id,
        cantidad,
        precio_unit
    )
    values (
        v_orden_id,
        p_producto_id,
        p_cantidad,
        p_precio_unit
    );

    -- Confirmar creación
    raise notice 'Orden creada con ID: %, total calculado: %', v_orden_id, v_total;

end;
$$;
