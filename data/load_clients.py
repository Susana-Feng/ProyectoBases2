import csv
import ast

from configs.connections import get_supabase_client, get_mongo_database, get_neo4j_driver, get_mssql_sales_engine
from datetime import datetime
from sqlalchemy import text

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

# Insercion a MSSQL
def cargar_csv_a_mssql(csv_file_path: str, table_name: str, batch_size: int = 500):
    """
    Inserta los datos de un CSV en una tabla SQL Server.
    - Evita duplicados (Email).
    - Inserta en batches para evitar el error 07002.
    """
    engine = get_mssql_sales_engine()

    # Leer CSV
    with open(csv_file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Leídas {len(rows)} filas del CSV")

    # Procesar filas
    data = []
    for row in rows:
        try:
            fecha_registro = datetime.strptime(row["FechaRegistro"], "%Y-%m-%d").date()
        except ValueError:
            print(f"⚠ Fecha inválida en fila: {row}")
            continue

        data.append({
            "Nombre": row["Nombre"].strip(),
            "Email": row["Email"].strip(),
            "Genero": row["Genero"].strip(),
            "Pais": row["Pais"].strip(),
            "FechaRegistro": fecha_registro
        })

    if not data:
        print("No hay datos válidos para insertar.")
        return

    with engine.begin() as conn:

        # Obtener emails existentes
        result = conn.execute(text(f"SELECT Email FROM {table_name}"))
        existing_emails = {row["Email"] for row in result.mappings()}

        # Filtrar nuevos
        new_data = [row for row in data if row["Email"] not in existing_emails]

        if not new_data:
            print("Todos los registros del CSV ya existen en la base.")
            return

        print(f"Registros nuevos a insertar: {len(new_data)}")

        # Query parametrizada estándar
        insert_query = text(f"""
            INSERT INTO {table_name} (Nombre, Email, Genero, Pais, FechaRegistro)
            VALUES (:Nombre, :Email, :Genero, :Pais, :FechaRegistro)
        """)

        # Insertar en lotes
        batch = []
        inserted_count = 0

        for row in new_data:
            batch.append(row)
            if len(batch) >= batch_size:
                conn.execute(insert_query, batch)
                inserted_count += len(batch)
                batch.clear()

        # Insertar el lote final
        if batch:
            conn.execute(insert_query, batch)
            inserted_count += len(batch)

        print(f"Insertados correctamente: {inserted_count} registros (sin duplicados)")

def main():
    # Supabase
    clients_supabase = "./clients/supabase/clients_supabase.csv"
    # cargar_csv_a_supabase(clients_supabase)
    print("Clientes cargados a supabase")

    # Mongo
    clients_mongo = "./clients/mongo/clients_mongo.csv"
    # cargar_csv_a_mongo(clients_mongo, "clientes")
    print("Clientes cargados a mongo")

    # Neo4j
    clients_neo4j = "./clients/neo4j/clients_neo4j.csv"
    #cargar_csv_a_neo4j(clients_neo4j)
    print("Clientes cargados a neo4j")

    # MSSQL
    clients_mssql = "./clients/mssql/clients_mssql.csv"
    cargar_csv_a_mssql(clients_mssql, "Cliente") 
    print("Clientes cargados a mssql")

if __name__ == "__main__":
    main()