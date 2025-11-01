-- ===========================================
-- Funcion: fn_eliminar_orden
-- Elimina una orden y su detalle automáticamente
-- ===========================================

create or replace function public.fn_eliminar_orden(
    p_orden_id uuid
)
returns boolean
language plpgsql
as $$
declare
    v_exist boolean;
begin
    -- Verificar si la orden existe
    select exists(select 1 from public.orden where orden_id = p_orden_id)
    into v_exist;

    if not v_exist then
        raise exception 'La orden con ID % no existe.', p_orden_id;
    end if;

    -- Eliminar detalles asociados
    delete from public.orden_detalle
    where orden_id = p_orden_id;

    -- Eliminar la orden principal
    delete from public.orden
    where orden_id = p_orden_id;

    -- Confirmar operación exitosa
    return true;
end;
$$;
