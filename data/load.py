from neo4j import GraphDatabase
NEO4J_URI="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="YnD8GV2PiuGD9rehQvdH"

def get_neo4j_driver():
    uri = NEO4J_URI
    user = NEO4J_USERNAME
    password = NEO4J_PASSWORD

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

def load_cypher_file(cypher_file: str):
    """
    Lee un archivo .cypher y ejecuta cada instrucción en Neo4j.
    Acepta múltiples sentencias separadas por ';'.
    """

    # Crear driver
    driver = get_neo4j_driver()

    # Leer archivo completo
    with open(cypher_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Separar sentencias por ';'
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]

    print(f"Ejecutando {len(statements)} sentencias Cypher...\n")

    with driver.session() as session:
        for idx, stmt in enumerate(statements, start=1):
            try:
                session.run(stmt)
                #print(f"[OK] Sentencia {idx} ejecutada.")
            except Exception as e:
                print(f"[ERROR] Sentencia {idx} falló:\n{stmt}\nError: {e}\n")

    driver.close()
    print("\nCarga finalizada.")

load_cypher_file(
    cypher_file=r"C:\Users\User\OneDrive\Desktop\Bases de Datos II\ProyectoBases2\data\out\neo4j_data.cypher"
)