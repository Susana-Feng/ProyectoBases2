CREATE  VIEW orden_completa
as

SELECT o.fecha as fecha,
o.canal as canal,
o.moneda as moneda,
o.total as total,
d.cantidad as cantidad,
d.precio_unit as precio_unitario,
p.nombre as nombre_producto,
c.nombre as nombre_cliente
FROM orden AS O
INNER JOIN orden_detalle AS D
ON O.orden_id = D.orden_id
INNER JOIN producto AS P
ON P.producto_id = D.producto_id
INNER JOIN cliente AS C
ON C.cliente_id = O.cliente_id