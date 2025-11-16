from extract.mongo import extract_mongo



if __name__ == "__main__":
    objetos_mongo = extract_mongo()

    print(f"Productos de Mongo:\n {list(objetos_mongo[0])}\n ")
    print(f"Clientes de Mongo:\n {list(objetos_mongo[1])}\n ")
    print(f"Órdenes de Mongo:\n {list(objetos_mongo[2])}\n ")