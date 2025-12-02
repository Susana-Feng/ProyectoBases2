from config.database import get_neo4j_driver

driver = get_neo4j_driver()

readProductsQuery = """
MATCH (p:Producto)-[:PERTENECE_A]->(cat:Categoria)
RETURN 
  p.id AS id,
  p.nombre AS nombre,
  p.sku AS sku,
  p.codigo_alt AS codigo_alt,
  p.codigo_mongo AS codigo_mongo,
  cat.id AS categoria_id,
  cat.nombre AS categoria
ORDER BY p.nombre ASC;
"""


class ProductRepository:
    @staticmethod
    def read_products():
        with driver.session() as session:
            try:
                result = session.run(readProductsQuery)
                return [record.data() for record in result]
            except Exception as e:
                print(f"Error in read_products: {e}")
                return []
