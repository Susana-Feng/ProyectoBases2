from config.database import get_neo4j_driver

driver = get_neo4j_driver()

readClientsQuery = """
MATCH (c:Cliente)
RETURN 
  c.id AS id,
  c.nombre AS nombre,
  c.genero AS genero,
  c.pais AS pais
ORDER BY c.nombre ASC;
"""


class ClientRepository:
    @staticmethod
    def read_clients():
        with driver.session() as session:
            try:
                result = session.run(readClientsQuery)
                return [record.data() for record in result]
            except Exception as e:
                print(f"Error in read_clients: {e}")
                return []
