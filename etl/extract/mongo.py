from configs.connections import get_mongo_database

db = get_mongo_database()

products_collection = db["productos"]
clients_collection = db["clientes"]
orders_collection = db["ordenes"]

def extract_mongo():
    lista_productos = products_collection.find()
    lista_clientes = clients_collection.find()
    lista_ordenes = orders_collection.find()

    return lista_productos, lista_clientes, lista_ordenes