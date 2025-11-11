from datetime import datetime, date
from config.database import get_neo4j_driver

driver = get_neo4j_driver()

# --------------------------------------------------
# CRUD Queries 
# --------------------------------------------------

# Queries actualizadas para retornar valores simples
createOrderQuery = '''
// Crear la orden
CREATE (o:Orden {
  id: $id,
  fecha: datetime($fecha),
  canal: $canal,
  moneda: $moneda,
  total: $total
})

// Relacionar con el cliente
WITH o
MATCH (c:Cliente {id: $cliente_id})
CREATE (c)-[:REALIZO]->(o)

// Crear relaciones con productos
WITH o
UNWIND $items AS item
MATCH (p:Producto {id: item.producto_id})
CREATE (o)-[r:CONTIENE {
  cantidad: item.cantidad,
  precio_unit: item.precio_unit
}]->(p)

// Retornar solo un valor simple para confirmación
RETURN "success" AS result;
'''

updateOrderRelationshipsQuery = '''
// Actualizar la orden
MATCH (o:Orden {id: $id})
SET o.fecha = datetime($fecha),
    o.canal = $canal,
    o.moneda = $moneda,
    o.total = $total

// Eliminar relaciones de productos existentes
WITH o
MATCH (o)-[r:CONTIENE]->()
DELETE r

// Crear nuevas relaciones con productos
WITH o
UNWIND $items AS item
MATCH (p:Producto {id: item.producto_id})
CREATE (o)-[r:CONTIENE {
  cantidad: item.cantidad,
  precio_unit: item.precio_unit
}]->(p)

// Retornar algo simple o nada
RETURN true as success;
'''

readOrdersQuery = '''
MATCH (c:Cliente)-[:REALIZO]->(o:Orden)-[r:CONTIENE]->(p:Producto)-[:PERTENECE_A]->(cat:Categoria)
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
ORDER BY o.fecha ASC
SKIP $skip
LIMIT $limit;
'''


readOrderByIdQuery = '''
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
'''

deleteOrderQuery = '''
MATCH (o:Orden {id: $id})
DETACH DELETE o;
'''

getLastId = """
        MATCH (o:Orden)
        WHERE o.id STARTS WITH 'O'
        RETURN o.id AS last_id
        ORDER BY o.id DESC
        LIMIT 1
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
                # Ejecutar la consulta y consumir el resultado inmediatamente
                result = session.run(
                    createOrderQuery,
                    id=id,
                    cliente_id=cliente_id,
                    fecha=fecha,
                    canal=canal,
                    moneda=moneda,
                    total=total,
                    items=items
                )
                
                # Consumir el resultado dentro del contexto de la sesión
                records = list(result)
                return len(records) > 0  # Retorna True si se creó al menos un registro
                
        except Exception as e:
            print(f"Error in create_order: {e}")
            return False

    @staticmethod
    def read_orders(skip: int = 0, limit: int = 20):
        with driver.session() as session:
            try:
                result = session.run(
                    readOrdersQuery,
                    skip=skip,
                    limit=limit
                )
                return [record.data() for record in result]
            except Exception as e:
                print(f"Error in read_orders: {e}")
                return []


    @staticmethod
    def read_order_by_id(order_id):
        with driver.session() as session:
            try:
                result = session.run(readOrderByIdQuery, id=order_id)
                # Convertir a lista DENTRO de la sesión
                return [record.data() for record in result]
            except Exception as e:
                print(f"Error in read_order_by_id: {e}")
                return []

    @staticmethod
    def delete_order(id):
        with driver.session() as session:
            try:
                session.execute_write(lambda tx: tx.run(deleteOrderQuery, id=id))
                return True
            except Exception as e:
                print(f"Error in delete_order: {e}")
                return False

    @staticmethod
    def update_order_with_relationships(id, fecha, canal, moneda, total, items):
        """Versión simplificada que solo ejecuta sin retornar resultados"""
        if isinstance(fecha, datetime):
            fecha = fecha.isoformat()
        elif isinstance(fecha, date):
            fecha = datetime(fecha.year, fecha.month, fecha.day).isoformat()

        try:
            with driver.session() as session:
                def update_order_tx(tx):
                    tx.run(
                        updateOrderRelationshipsQuery,
                        id=id,
                        fecha=fecha,
                        canal=canal,
                        moneda=moneda,
                        total=total,
                        items=items
                    )
                    return True
                
                session.execute_write(update_order_tx)
                return True
                
        except Exception as e:
            print(f"Error in update_order_with_relationships: {e}")
            return False
    @staticmethod
    def get_last_order_id():
        """Obtiene el último ID de orden numéricamente"""

        with driver.session() as session:
            result = session.run(getLastId)
            record = result.single()
            return record["last_id"] if record else None