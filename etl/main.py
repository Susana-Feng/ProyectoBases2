from extract.mongo import extract_mongo
from transform.mongo import transform_mongo
from load.general import load_datawarehouse

if __name__ == "__main__":
    
    # Extracciones de bases de datos
    objetos_mongo = extract_mongo()

    # Transformaciones de datos
    transform_mongo(objetos_mongo[0], objetos_mongo[1], objetos_mongo[2])

    # Carga general del datawarehouse
    load_datawarehouse()

    #pd: aun no se aplican los tipos de cambios pq no se como está el estado del job en stg.orden_items

    # Función para resetear el DataWarehouse (eliminar datos cargados de prueba)
    def reset_datawarehouse():
        from sqlalchemy import text
        from configs.connections import get_dw_engine
        engine = get_dw_engine()
        sql = """
            delete from dw.FactVentas
            delete from dw.DimProducto
            delete from dw.DimCliente
            delete from dw.DimTiempo
            delete from stg.map_producto
            delete from stg.orden_items
            delete from stg.clientes
        """

        with engine.begin() as conn:
            conn.execute(text(sql))

    #reset_datawarehouse()


    