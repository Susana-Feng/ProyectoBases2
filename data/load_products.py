import csv
import ast
from typing import List, Dict, Any

from configs.connections import (
    get_supabase_client,
    get_mongo_database,
    get_neo4j_driver,
    get_mssql_sales_engine,
)
from sqlalchemy import text


# =========================
#   Supabase: tabla producto
# =========================
def cargar_productos_supabase(csv_file_path: str, table_name: str = "producto") -> None:
    """
    Carga productos desde un CSV a la tabla `producto` en Supabase.
    - Evita duplicados por SKU (cuando no está vacío).
    - Para filas sin SKU, evita duplicados por (nombre, categoria).
    """
    supabase = get_supabase_client()

    with open(csv_file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[Supabase] Leídas {len(rows)} filas del CSV")

    registros: List[Dict[str, Any]] = []
    omitidos = 0

    for row in rows:
        sku = (row.get("sku") or "").strip()
        nombre = (row.get("nombre") or "").strip()
        categoria = (row.get("categoria") or "").strip()

        if not nombre or not categoria:
            print(f"⚠ Fila sin nombre o categoría, se omite: {row}")
            omitidos += 1
            continue

        # Evitar duplicados
        if sku:
            existente = (
                supabase.table(table_name)
                .select("sku")
                .eq("sku", sku)
                .execute()
            )
            if existente.data:
                omitidos += 1
                continue
        else:
            # SKU vacío: controlar duplicados por nombre + categoría
            existente = (
                supabase.table(table_name)
                .select("nombre", "categoria")
                .eq("nombre", nombre)
                .eq("categoria", categoria)
                .execute()
            )
            if existente.data:
                omitidos += 1
                continue

        registros.append(
            {
                "sku": sku or None,
                "nombre": nombre,
                "categoria": categoria,
            }
        )

    if registros:
        supabase.table(table_name).insert(registros).execute()
        print(
            f"[Supabase] Insertados correctamente {len(registros)} registros. Omitidos: {omitidos}"
        )
    else:
        print("[Supabase] No hay registros nuevos para insertar.")


# ======================
#   MongoDB: colección
# ======================
def cargar_productos_mongo(csv_file_path: str, collection_name: str = "productos") -> None:
    """
    Carga productos desde un CSV a MongoDB.
    - Usa `codigo_mongo` como identificador único.
    - Parsea la columna `equivalencias` (string → dict).
    """
    db = get_mongo_database()
    collection = db[collection_name]

    with open(csv_file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[Mongo] Leídas {len(rows)} filas del CSV")

    documentos: List[Dict[str, Any]] = []
    omitidos = 0

    for row in rows:
        codigo_mongo = (row.get("codigo_mongo") or "").strip()
        nombre = (row.get("nombre") or "").strip()
        categoria = (row.get("categoria") or "").strip()
        equivalencias_raw = row.get("equivalencias", "")

        if not codigo_mongo or not nombre or not categoria:
            print(f"⚠ Fila inválida (falta codigo_mongo/nombre/categoria), se omite: {row}")
            omitidos += 1
            continue

        # Evitar duplicados por codigo_mongo
        if collection.find_one({"codigo_mongo": codigo_mongo}):
            omitidos += 1
            continue

        # Parsear equivalencias
        try:
            equivalencias = ast.literal_eval(equivalencias_raw)
            if not isinstance(equivalencias, dict):
                raise ValueError("equivalencias no es dict")
        except Exception:
            print(
                f"⚠ Error parseando equivalencias: {equivalencias_raw} → se omite fila"
            )
            omitidos += 1
            continue

        doc = {
            "codigo_mongo": codigo_mongo,
            "nombre": nombre,
            "categoria": categoria,
            "equivalencias": equivalencias,
        }
        documentos.append(doc)

    if documentos:
        result = collection.insert_many(documentos)
        print(
            f"[Mongo] Insertados correctamente {len(result.inserted_ids)} documentos. Omitidos: {omitidos}"
        )
    else:
        print("[Mongo] No se insertó ningún documento.")


# ======================
#   Neo4j: nodos Producto
# ======================
def insertar_producto(tx, producto: Dict[str, Any]) -> None:
    """
    Inserta o actualiza un nodo Producto en Neo4j.
    Usa `id` como clave de MERGE (derivada de codigo_mongo por defecto).
    """
    query = """
    MERGE (p:Producto {id: $id})
    SET p.nombre       = $nombre,
        p.categoria    = $categoria,
        p.sku          = $sku,
        p.codigo_alt   = $codigo_alt,
        p.codigo_mongo = $codigo_mongo
    """
    tx.run(query, **producto)


def cargar_productos_neo4j(csv_file_path: str) -> None:
    """
    Carga productos desde un CSV a Neo4j como nodos Producto.
    """
    driver = get_neo4j_driver()

    with driver.session() as session:
        with open(csv_file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            count = 0
            for row in reader:
                sku = (row.get("sku") or "").strip()
                codigo_alt = (row.get("codigo_alt") or "").strip()
                codigo_mongo = (row.get("codigo_mongo") or "").strip()
                nombre = (row.get("nombre") or "").strip()
                categoria = (row.get("categoria") or "").strip()

                if not nombre or not categoria:
                    print(f"⚠ Fila inválida (sin nombre/categoría), se omite: {row}")
                    continue

                # Se toma codigo_mongo como id principal; si por alguna razón está vacío,
                # se usan sku o codigo_alt como respaldo.
                id_producto = codigo_mongo or sku or codigo_alt
                if not id_producto:
                    print(f"⚠ Fila sin identificador usable, se omite: {row}")
                    continue

                producto = {
                    "id": id_producto,
                    "sku": sku or None,
                    "codigo_alt": codigo_alt or None,
                    "codigo_mongo": codigo_mongo or None,
                    "nombre": nombre,
                    "categoria": categoria,
                }

                session.execute_write(insertar_producto, producto)
                count += 1

    driver.close()
    print(f"[Neo4j] Datos cargados correctamente. Nodos procesados: {count}")


# ===========================
#   MSSQL: tabla Producto
# ===========================
def cargar_productos_mssql(
    csv_file_path: str,
    table_name: str = "dbo.Producto",
    batch_size: int = 500,
) -> None:
    """
    Inserta productos desde un CSV en una tabla SQL Server.
    - Evita duplicados por SKU.
    - Inserta en batches para evitar problemas de parámetros.
    """
    engine = get_mssql_sales_engine()

    with open(csv_file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[MSSQL] Leídas {len(rows)} filas del CSV")

    data: List[Dict[str, Any]] = []
    for row in rows:
        sku = (row.get("sku") or "").strip()
        nombre = (row.get("nombre") or "").strip()
        categoria = (row.get("categoria") or "").strip()

        if not sku or not nombre or not categoria:
            print(f"⚠ Fila inválida (falta SKU/nombre/categoría), se omite: {row}")
            continue

        data.append(
            {
                "SKU": sku,
                "Nombre": nombre,
                "Categoria": categoria,
            }
        )

    if not data:
        print("[MSSQL] No hay datos válidos para insertar.")
        return

    with engine.begin() as conn:
        # Obtener SKUs existentes
        result = conn.execute(text(f"SELECT SKU FROM {table_name}"))
        existing_skus = {row["SKU"] for row in result.mappings()}

        # Filtrar nuevos
        new_data = [row for row in data if row["SKU"] not in existing_skus]

        if not new_data:
            print("[MSSQL] Todos los registros del CSV ya existen en la base.")
            return

        print(f"[MSSQL] Registros nuevos a insertar: {len(new_data)}")

        insert_query = text(
            f"""
            INSERT INTO {table_name} (SKU, Nombre, Categoria)
            VALUES (:SKU, :Nombre, :Categoria)
        """
        )

        inserted_count = 0
        batch: List[Dict[str, Any]] = []

        for row in new_data:
            batch.append(row)
            if len(batch) >= batch_size:
                conn.execute(insert_query, batch)
                inserted_count += len(batch)
                batch = []

        if batch:
            conn.execute(insert_query, batch)
            inserted_count += len(batch)

        print(f"[MSSQL] Insertados correctamente: {inserted_count} registros.")


def main() -> None:
    # Rutas por defecto según el generador `gen_products_data.py`
    products_supabase = r".\products\supabase\products_supabase.csv"
    products_mongo = r".\products\mongo\products_mongo.csv"
    products_neo4j = r".\products\neo4j\products_neo4j.csv"
    products_mssql = r".\products\mssql\products_mssql.csv"
    # Descomentar según la carga que se desee realizar:

    # Supabase
    cargar_productos_supabase(products_supabase)
    print("Productos cargados a Supabase")

    # Mongo
    cargar_productos_mongo(products_mongo, "productos")
    print("Productos cargados a MongoDB")

    # Neo4j
    cargar_productos_neo4j(products_neo4j)
    print("Productos cargados a Neo4j")

    # MSSQL
    cargar_productos_mssql(products_mssql, "dbo.Producto")
    print("Productos cargados a MSSQL")


if __name__ == "__main__":
    main()
