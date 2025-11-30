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

    # Count total items from orders
    total_items = sum(len(orden.get("items", [])) for orden in lista_ordenes)

    print(
        f"    mongo: {len(lista_clientes)} clients | {len(lista_productos)} products | {len(lista_ordenes)} orders | {total_items} items"
    )

    return lista_productos, lista_clientes, lista_ordenes
