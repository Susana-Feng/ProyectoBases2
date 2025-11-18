from configs.connections import get_mongo_database

db = get_mongo_database()

products_collection = db["productos"]
clients_collection = db["clientes"]
orders_collection = db["ordenes"]


def extract_mongo():
    """
    Extrae datos de MongoDB y los convierte a listas para poder procesarlos múltiples veces.
    Retorna tupla: (lista_productos, lista_clientes, lista_ordenes)
    """
    # Convertir cursores a listas para poder iterar múltiples veces
    lista_productos = list(products_collection.find())
    lista_clientes = list(clients_collection.find())
    lista_ordenes = list(orders_collection.find())

    # Mostrar estadísticas de extracción
    print(f"[MongoDB Extract] Productos extraídos: {len(lista_productos)}")
    print(f"[MongoDB Extract] Clientes extraídos: {len(lista_clientes)}")
    print(f"[MongoDB Extract] Órdenes extraídas: {len(lista_ordenes)}")

    return lista_productos, lista_clientes, lista_ordenes
