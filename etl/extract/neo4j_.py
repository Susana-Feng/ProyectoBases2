from configs.connections import get_neo4j_driver

def extract_neo4j():
    """
    Extrae nodos y relaciones desde Neo4j.
    Devuelve un diccionario:
    {
        "nodes": {
            "Label1": [ {...}, {...} ],
            "Label2": [ {...} ]
        },
        "relationships": {
            "REL_TYPE": [
                {
                    "from_label": str,
                    "from": {props},
                    "to_label": str,
                    "to": {props},
                    "properties": {props}
                }
            ]
        }
    }
    """
    driver = get_neo4j_driver()

    with driver.session() as session:

        # ---------------------------------------
        # 1. EXTRAER NODOS
        # ---------------------------------------
        labels = session.run("CALL db.labels()").value()
        nodes_by_label = {}

        for label in labels:
            query = f"MATCH (n:{label}) RETURN n"
            result = session.run(query)

            nodes = []
            for record in result:
                node = record["n"]
                nodes.append(dict(node))

            nodes_by_label[label] = nodes
            print(f"[Neo4j Extract] {label}: {len(nodes)} nodos extraídos")


        # ---------------------------------------
        # 2. EXTRAER RELACIONES
        # ---------------------------------------
        relationships_by_type = {}

        rel_result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN labels(a) AS from_labels,
                   a AS from_node,
                   type(r) AS rel_type,
                   r AS rel_props,
                   labels(b) AS to_labels,
                   b AS to_node
        """)

        for record in rel_result:
            rel_type = record["rel_type"]

            if rel_type not in relationships_by_type:
                relationships_by_type[rel_type] = []

            relationships_by_type[rel_type].append({
                "from_label": record["from_labels"][0],
                "from": dict(record["from_node"]),
                "to_label": record["to_labels"][0],
                "to": dict(record["to_node"]),
                "properties": dict(record["rel_props"])
            })

        for rel_type, rels in relationships_by_type.items():
            print(f"[Neo4j Extract] {rel_type}: {len(rels)} relaciones extraídas")


    driver.close()

    return {
        "nodes": nodes_by_label,
        "relationships": relationships_by_type
    }