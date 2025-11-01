drop view if exists public.orden_completa;

create view public.orden_completa as
select 
    o.orden_id,
    o.fecha,
    o.canal,
    o.moneda,
    o.total,
    d.cantidad,
    d.precio_unit as precio_unitario,
    p.producto_id,
    c.cliente_id, 
    p.nombre as nombre_producto,
    c.nombre as nombre_cliente
from public.orden o
inner join public.orden_detalle d on o.orden_id = d.orden_id
inner join public.producto p on p.producto_id = d.producto_id
inner join public.cliente c on c.cliente_id = o.cliente_id;