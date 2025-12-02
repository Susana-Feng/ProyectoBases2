import logging
from datetime import datetime, date
from config.database import get_neo4j_driver

driver = get_neo4j_driver()
logger = logging.getLogger(__name__)

# --------------------------------------------------
# CRUD Queries
# --------------------------------------------------

# Queries actualizadas para retornar valores simples
createOrderQuery = """
MATCH (c:Cliente)
WHERE toString(c.id) = toString($cliente_id)
CREATE (o:Orden {
    id: $id,
    fecha: datetime($fecha),
    canal: $canal,
    moneda: $moneda,
    total: $total
})
CREATE (c)-[:REALIZO]->(o)
WITH o, $items AS items
UNWIND items AS item
MATCH (p:Producto)
WHERE toString(p.id) = toString(item.producto_id)
CREATE (o)-[:CONTIENE {
    cantidad: item.cantidad,
    precio_unit: item.precio_unit
}]->(p)
RETURN DISTINCT o.id AS orden_id;
"""

updateOrderRelationshipsQuery = """
MATCH (c:Cliente)
WHERE toString(c.id) = toString($cliente_id)
OPTIONAL MATCH (old:Orden {id: $id})
DETACH DELETE old

CREATE (o:Orden {
    id: $id,
    fecha: datetime($fecha),
    canal: $canal,
    moneda: $moneda,
    total: $total
})
CREATE (c)-[:REALIZO]->(o)
WITH o, $items AS items
UNWIND items AS item
MATCH (p:Producto)
WHERE toString(p.id) = toString(item.producto_id)
CREATE (o)-[:CONTIENE {
    cantidad: item.cantidad,
    precio_unit: item.precio_unit
}]->(p)
RETURN DISTINCT o.id AS orden_id;
"""

readOrdersQuery = """
MATCH (c:Cliente)-[:REALIZO]->(o:Orden)
WITH c, o
ORDER BY o.fecha ASC
SKIP $skip
LIMIT $limit
OPTIONAL MATCH (o)-[r:CONTIENE]->(p:Producto)-[:PERTENECE_A]->(cat:Categoria)
RETURN 
    o.id AS orden_id,
    o.fecha AS fecha,
    o.canal AS canal,
    o.moneda AS moneda,
    o.total AS total,
    c.id AS cliente_id,
    c.nombre AS cliente_nombre,
    c.genero AS genero,
    c.pais AS pais,
    p.id AS producto_id,
    p.nombre AS producto_nombre,
    cat.id AS categoria_id,
    cat.nombre AS categoria,
    r.cantidad AS cantidad,
    r.precio_unit AS precio_unit,
    (r.cantidad * r.precio_unit) AS subtotal
ORDER BY o.fecha ASC;
"""


readOrderByIdQuery = """
MATCH (c:Cliente)-[:REALIZO]->(o:Orden {id: $id})-[r:CONTIENE]->(p:Producto)-[:PERTENECE_A]->(cat:Categoria)
RETURN 
  o.id AS orden_id,
  o.fecha AS fecha,
  o.canal AS canal,
  o.moneda AS moneda,
  o.total AS total,
  c.id AS cliente_id,
  c.nombre AS cliente_nombre,
  c.genero AS genero,
  c.pais AS pais,
  p.id AS producto_id,
  p.nombre AS producto_nombre,
  cat.id AS categoria_id,
  cat.nombre AS categoria,
  r.cantidad AS cantidad,
  r.precio_unit AS precio_unit,
  (r.cantidad * r.precio_unit) AS subtotal
ORDER BY o.fecha ASC;
"""

deleteOrderQuery = """
MATCH (o:Orden {id: $id})
DETACH DELETE o;
"""

getLastId = """
MATCH (o:Orden)
WHERE o.id =~ 'ORD-\\d+' OR o.id =~ 'O\\d+'
RETURN o.id AS last_id,
CASE
    WHEN o.id STARTS WITH 'ORD-' THEN toInteger(replace(o.id, 'ORD-', ''))
    WHEN o.id STARTS WITH 'O' THEN toInteger(substring(o.id, 1))
    ELSE 0
END AS numeric_id
ORDER BY numeric_id DESC
LIMIT 1
"""

clientExistsQuery = """
MATCH (c:Cliente)
WHERE toString(c.id) = toString($cliente_id)
RETURN c.id AS id
LIMIT 1;
"""

productsExistQuery = """
UNWIND $producto_ids AS pid
MATCH (p:Producto)
WHERE toString(p.id) = toString(pid)
RETURN collect(DISTINCT toString(p.id)) AS found_ids;
"""

countOrdersQuery = """
MATCH (o:Orden)
RETURN count(DISTINCT o.id) AS total;
"""


# --------------------------------------------------
# Class for CRUD operations on Orders
# --------------------------------------------------
class OrderRepository:
    @staticmethod
    def create_order(id, cliente_id, fecha, canal, moneda, total, items):
        """Crea una orden sin retornar resultados complejos"""
        if isinstance(fecha, datetime):
            fecha = fecha.isoformat()
        elif isinstance(fecha, date):
            fecha = datetime(fecha.year, fecha.month, fecha.day).isoformat()

        try:
            with driver.session() as session:
                result = session.run(
                    createOrderQuery,
                    id=id,
                    cliente_id=cliente_id,
                    fecha=fecha,
                    canal=canal,
                    moneda=moneda,
                    total=total,
                    items=items,
                )

                summary = result.consume()
                return summary.counters.nodes_created > 0

        except Exception:
            logger.exception("Error in create_order")
            return False

    @staticmethod
    def read_orders(skip: int = 0, limit: int = 20):
        with driver.session() as session:
            try:
                result = session.run(readOrdersQuery, skip=skip, limit=limit)
                return [record.data() for record in result]
            except Exception:
                logger.exception("Error in read_orders")
                return []

    @staticmethod
    def count_orders() -> int:
        with driver.session() as session:
            try:
                result = session.run(countOrdersQuery)
                record = result.single()
                return (
                    int(record["total"])
                    if record and record["total"] is not None
                    else 0
                )
            except Exception:
                logger.exception("Error in count_orders")
                return 0

    @staticmethod
    def read_order_by_id(order_id):
        with driver.session() as session:
            try:
                result = session.run(readOrderByIdQuery, id=order_id)
                # Convertir a lista DENTRO de la sesión
                return [record.data() for record in result]
            except Exception:
                logger.exception("Error in read_order_by_id")
                return []

    @staticmethod
    def delete_order(id):
        with driver.session() as session:
            try:
                session.execute_write(lambda tx: tx.run(deleteOrderQuery, id=id))
                return True
            except Exception:
                logger.exception("Error in delete_order")
                return False

    @staticmethod
    def update_order_with_relationships(
        id, fecha, canal, cliente_id, moneda, total, items
    ):
        if isinstance(fecha, datetime):
            fecha = fecha.isoformat()
        elif isinstance(fecha, date):
            fecha = datetime(fecha.year, fecha.month, fecha.day).isoformat()

        try:
            with driver.session() as session:
                result = session.run(
                    updateOrderRelationshipsQuery,
                    id=id,
                    cliente_id=cliente_id,
                    fecha=fecha,
                    canal=canal,
                    moneda=moneda,
                    total=total,
                    items=items,
                )

                summary = result.consume()
                # At least one order node plus relationships should be re-created
                return summary.counters.nodes_created > 0

        except Exception:
            logger.exception("Error in update_order_with_relationships")
            return False

    @staticmethod
    def get_last_order_id():
        """Obtiene el último ID de orden numéricamente"""

        with driver.session() as session:
            result = session.run(getLastId)
            record = result.single()
            return record["last_id"] if record else None

    @staticmethod
    def client_exists(cliente_id: str) -> bool:
        if not cliente_id:
            return False
        with driver.session() as session:
            result = session.run(clientExistsQuery, cliente_id=str(cliente_id))
            try:
                record = result.single()
            except Exception:
                return False
            return record is not None

    @staticmethod
    def missing_product_ids(product_ids):
        normalized = {str(pid).strip() for pid in product_ids if pid not in (None, "")}
        if not normalized:
            return []

        with driver.session() as session:
            result = session.run(productsExistQuery, producto_ids=list(normalized))
            record = result.single()
            data = record.data() if record else {}
            found_ids = set(data.get("found_ids", []) or [])

        missing = normalized - {str(fid).strip() for fid in found_ids}
        return sorted(missing)
