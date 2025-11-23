import csv
import os
import psycopg2

from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine
from neo4j import GraphDatabase

# Cargar variables de entorno
load_dotenv(".env.local")


# Variables de conexión Neo4j
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def get_neo4j_driver():
    uri = NEO4J_URI
    user = NEO4J_USERNAME
    password = NEO4J_PASSWORD

    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver


def insertar_cliente(tx, cliente):
    query = """
    MERGE (c:Cliente {id: $id})
    SET c.nombre = $nombre,
        c.genero = $genero,
        c.pais = $pais
    """
    tx.run(query, **cliente)


def cargar_csv_a_neo4j(csv_file):
    driver = get_neo4j_driver()

    with driver.session() as session:
        with open(csv_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                cliente = {
                    "id": row["id"],
                    "nombre": row["nombre"],
                    "genero": row["genero"],
                    "pais": row["pais"]
                }
                session.execute_write(insertar_cliente, cliente)

    driver.close()
    print("Datos cargados correctamente a Neo4j.")


def main():
    clients_neo4j = "./data/clients/neo4j/clients_neo4j.csv"
    cargar_csv_a_neo4j(clients_neo4j)
    print("Clientes cargados a neo4j")
    print(NEO4J_URI)

if __name__ == "__main__":
    main()