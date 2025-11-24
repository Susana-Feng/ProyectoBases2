import csv
import ast

from etl.configs.connections import get_supabase_client, get_mongo_database, get_neo4j_driver
from datetime import datetime

# Insercion a supabase
def cargar_csv_a_supabase(csv_file_path: str):
    # Conectar a Supabase con tu función
    supabase = get_supabase_client()

    TABLE_NAME = "cliente"

    # Leer CSV
    with open(csv_file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Leídas {len(rows)} filas del CSV")

    registros = []
    omitidos = 0

    for row in rows:
        email = row["email"].strip()

        # Verificar si ese email ya existe en Supabase
        existente = supabase.table(TABLE_NAME).select("email").eq("email", email).execute()

        if existente.data: # si trae datos, ya existe
            print(f"El email ya exite, se omite: {email}")
            omitidos += 1
            continue
        
        # Validar la fecha
        try:
            fecha_registro = datetime.strptime(row["fecha_registro"], "%Y-%m-%d").date()
        except ValueError:
            print(f"⚠ Fecha inválida en fila: {row}")
            continue

        registros.append({
            "nombre": row["nombre"].strip(),
            "email": row["email"].strip(),
            "genero": row["genero"].strip(),
            "pais": row["pais"].strip(),
            "fecha_registro": fecha_registro.isoformat()
        })

    if registros:
        # Insertar en Supabase solo lo nuevo
        respuesta = supabase.table(TABLE_NAME).insert(registros).execute()
        print(f"Insertados correctamente: {len(registros)} registros")
    else:
        print("No hay registros nuevos para insertar.")

# Insercion a mongo
def cargar_csv_a_mongo(csv_file_path: str, collection_name: str):
    """
    Inserta datos desde un CSV a MongoDB usando la función de conexión get_mongo_database.
    """
    db = get_mongo_database()
    client_collection = db["clientes"]

    with open(csv_file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        registros = []

        for row in reader:
            email = row["email"].strip()

            # Verificar si ya existe el email
            if client_collection.find_one({"email": email}):
                print(f"Email ya existe, se omite: {email}")
                continue

            # Parsear preferencias de string a dict
            try:
                preferencias = ast.literal_eval(row["preferencias"])
            except Exception as e:
                print(f"⚠ Error parseando preferencias: {row['preferencias']} → se ignora fila")
                continue

            # Parsear fecha de creación
            try:
                creado = row["creado"]
                # Si viene en formato {"$date": "YYYY-MM-DD"}
                if creado.startswith("{"):
                    creado_dict = ast.literal_eval(creado)
                    creado = datetime.strptime(creado_dict["$date"], "%Y-%m-%d")
                else:
                    creado = datetime.strptime(creado, "%Y-%m-%d")
            except Exception as e:
                print(f"⚠ Fecha inválida: {row['creado']} → se ignora fila")
                continue

            registros.append({
                "nombre": row["nombre"].strip(),
                "email": row["email"].strip(),
                "genero": row["genero"].strip(),
                "pais": row["pais"].strip(),
                "preferencias": preferencias,
                "creado": creado
            })

    if registros:
        result = client_collection.insert_many(registros)
        print(f"Insertados correctamente {len(result.inserted_ids)} registros en '{collection_name}'")
    else:
        print("No se insertó ningún registro.")

# Insercion a neo4j
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
    # Supabase
    clients_supabase = "./data/clients/supabase/clients_supabase.csv"
    cargar_csv_a_supabase(clients_supabase)
    print("Clientes cargados a supabase")

    # Mongo
    clients_mongo = "./data/clients/mongo/clients_mongo.csv"
    cargar_csv_a_mongo(clients_mongo, "clientes")
    print("Clientes cargados a mongo")

    # Neo4j
    clients_neo4j = "./data/clients/neo4j/clients_neo4j.csv"
    cargar_csv_a_neo4j(clients_neo4j)
    print("Clientes cargados a neo4j")

if __name__ == "__main__":
    main()