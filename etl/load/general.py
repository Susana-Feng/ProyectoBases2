import pandas as pd
from configs.connections import get_dw_engine
from sqlalchemy import text
from datetime import datetime, timedelta

engine = get_dw_engine()

''' -----------------------------------------------------------------------
            Queries de SQL para cargar el DataWarehouse
    ----------------------------------------------------------------------- ''' 

query_check_last_load = """
    SELECT 
        COALESCE(MAX(LoadTS), '1900-01-01') AS LastLoadTS
    FROM {table_name}
"""

query_insert_DimTime = """
    DECLARE @FechaInicio DATE = '2022-01-01';
    DECLARE @FechaFin    DATE = CAST(GETDATE() AS DATE);

    ;WITH Fechas AS (
        SELECT @FechaInicio AS Fecha
        UNION ALL
        SELECT DATEADD(DAY, 1, Fecha)
        FROM Fechas
        WHERE Fecha < @FechaFin
    )
    INSERT INTO dw.DimTiempo (
        TiempoID, Fecha, Anio, Mes, Dia, LoadTS
    )
    SELECT
        CONVERT(INT, FORMAT(Fecha, 'yyyyMMdd')) AS TiempoID,
        Fecha,
        YEAR(Fecha) AS Anio,
        MONTH(Fecha) AS Mes,
        DAY(Fecha) AS Dia,
        GETDATE() AS LoadTS
    FROM Fechas
    OPTION (MAXRECURSION 0);
"""

query_insert_dimCliente_dw = """
    INSERT INTO dw.DimCliente (
        SourceSystem,
        SourceKey,
        Email,
        Nombre,
        Genero,
        Pais,
        FechaCreacionID,
        LoadTS
    )
    SELECT
        :sourceSystem,
        :sourceKey,
        :Email,
        :Nombre,
        :Genero,
        :Pais,
        TiempoID,
        GETDATE() AS LoadTS
    FROM dw.DimTiempo
    WHERE Fecha = :FechaCreacion;
"""

query_select_clientes_stg = """
    SELECT
        C.source_system AS sourceSystem,
        C.source_code AS sourceCode,
        C.cliente_email AS Email,
        C.cliente_nombre AS Nombre,
        C.genero_norm AS Genero,
        C.pais_raw AS Pais,
        C.fecha_creado_dt AS FechaCreacion,
        C.load_ts AS SourceLoadTS
    FROM stg.clientes AS C
    WHERE C.load_ts > :last_load_ts
"""

query_select_map_producto = """
    SELECT
        P.source_system AS SourceSystem,
        P.source_code AS SourceKey,
        P.nombre_norm AS Nombre,
        P.categoria_norm AS Categoria,
        P.es_servicio AS EsServicio,
        P.sku_oficial AS SKU
    FROM stg.map_producto AS P
"""

query_select_map_producto_new = """
    SELECT
        P.source_system AS SourceSystem,
        P.source_code AS SourceKey,
        P.nombre_norm AS Nombre,
        P.categoria_norm AS Categoria,
        P.es_servicio AS EsServicio,
        P.sku_oficial AS SKU
    FROM stg.map_producto AS P
    WHERE NOT EXISTS (
        SELECT 1 FROM dw.DimProducto dp 
        WHERE dp.SourceSystem = P.source_system 
        AND dp.SourceKey = P.source_code
    )
"""

query_insert_dimProducto_dw = """
    INSERT INTO dw.DimProducto (
        SKU,
        Nombre,
        Categoria,
        EsServicio,
        SourceSystem,
        SourceKey,
        LoadTS
    )
    VALUES (
        :SKU,
        :Nombre,
        :Categoria,
        :EsServicio,
        :SourceSystem,
        :SourceKey,
        GETDATE()
    )
"""

query_insert_factVentas = """
    INSERT INTO dw.FactVentas(
        TiempoID,
        ClienteID,
        ProductoID,
        Canal,
        Fuente,
        Cantidad,
        PrecioUnitUSD,
        TotalUSD,
        MonedaOriginal,
        PrecioUnitOriginal,
        TotalOriginal,
        SourceKey,
        LoadTS
    )
    SELECT
        T.TiempoID,
        C.ClienteID,
        P.ProductoID,
        O.canal_raw,
        O.source_system,
        O.cantidad_num,
        O.precio_unit_num,
        O.total_num,
        O.moneda,
        O.precio_unit_raw,
        O.total_raw,
        O.source_key_orden,
        GETDATE() AS LoadTS
    FROM
        dw.DimTiempo AS T,
        stg.orden_items AS O
    INNER JOIN dw.DimCliente AS C
        ON O.cliente_key = C.SourceKey
    INNER JOIN dw.DimProducto AS P
        ON O.source_code_prod = P.SourceKey
    WHERE
        T.Fecha = O.fecha_dt
        AND O.load_ts > :last_load_ts
"""

query_select_new_orders = """
    SELECT COUNT(*) AS NewRecords
    FROM stg.orden_items
    WHERE load_ts > :last_load_ts
"""

query_check_existing_product = """
    SELECT COUNT(*) 
    FROM dw.DimProducto 
    WHERE SourceSystem = :SourceSystem AND SourceKey = :SourceKey
"""

''' -----------------------------------------------------------------------
            Funciones auxiliares para cargar el DataWarehouse
    ----------------------------------------------------------------------- ''' 

def get_last_load_timestamp(conn, table_name):
    """Obtiene el último timestamp de carga de una tabla del DW"""
    query = text(query_check_last_load.format(table_name=table_name))
    result = conn.execute(query)
    last_load = result.fetchone()[0]
    return last_load

def should_run_process(conn):
    """Verifica si el proceso debe ejecutarse basado en los últimos LoadTS"""
    
    # Obtener el último LoadTS de cada dimensión
    last_load_tiempo = get_last_load_timestamp(conn, "dw.DimTiempo")
    last_load_cliente = get_last_load_timestamp(conn, "dw.DimCliente")
    last_load_producto = get_last_load_timestamp(conn, "dw.DimProducto")
    last_load_ventas = get_last_load_timestamp(conn, "dw.FactVentas")
    
    # Verificar si hay datos nuevos en las tablas de staging
    current_time = datetime.now()
    
    # Si alguna dimensión no tiene datos recientes (menos de 24 horas), ejecutar
    time_threshold = current_time - timedelta(hours=24)
    
    if (last_load_tiempo < time_threshold or 
        last_load_cliente < time_threshold or 
        last_load_producto < time_threshold or 
        last_load_ventas < time_threshold):
        return True, "Proceso programado (más de 24 horas desde última ejecución)"
    
    # Verificar si hay nuevos datos en las tablas de staging
    try:
        # Verificar nuevas órdenes
        result = conn.execute(text(query_select_new_orders), 
                            {'last_load_ts': last_load_ventas})
        new_orders = result.fetchone()[0]
        
        if new_orders > 0:
            return True, f"Se encontraron {new_orders} nuevas órdenes para procesar"
            
        # Verificar nuevos clientes
        result = conn.execute(text(query_select_clientes_stg), 
                            {'last_load_ts': last_load_cliente})
        new_clientes = len(result.fetchall())
        
        if new_clientes > 0:
            return True, f"Se encontraron {new_clientes} nuevos clientes para procesar"
            
    except Exception as e:
        print(f"Error en verificación: {e}")
        # Si hay error en la verificación, ejecutar el proceso por seguridad
        return True, "Error en verificación, ejecutando proceso por seguridad"
    
    return False, "No hay datos nuevos para procesar"

def get_clientes_stg(conn, last_load_ts):
    """Obtiene clientes nuevos desde el staging"""
    result = conn.execute(text(query_select_clientes_stg), 
                         {'last_load_ts': last_load_ts})
    clientes_stg = result.fetchall()
    return clientes_stg

def get_map_productos(conn):
    """Obtiene todos los productos desde el staging (sin load_ts)"""
    result = conn.execute(text(query_select_map_producto))
    productos_stg = result.fetchall()
    return productos_stg

def get_new_map_productos(conn):
    """Obtiene solo productos nuevos que no existen en el DW"""
    result = conn.execute(text(query_select_map_producto_new))
    productos_stg = result.fetchall()
    return productos_stg

def product_exists(conn, source_system, source_key):
    """Verifica si un producto ya existe en el DW"""
    result = conn.execute(text(query_check_existing_product), {
        'SourceSystem': source_system,
        'SourceKey': source_key
    })
    return result.fetchone()[0] > 0

def load_dim_tiempo(conn):
    """Carga DimTiempo solo si es necesario"""
    # Verificar si ya tenemos fechas hasta hoy
    query_check_dates = """
        SELECT MAX(Fecha) AS MaxFecha 
        FROM dw.DimTiempo
        WHERE Fecha <= CAST(GETDATE() AS DATE)
    """
    result = conn.execute(text(query_check_dates))
    max_fecha = result.fetchone()[0]
    
    current_date = datetime.now().date()
    
    if max_fecha and max_fecha >= current_date:
        print("DimTiempo ya está actualizado hasta la fecha actual")
        return False
    else:
        print("Actualizando DimTiempo...")
        conn.exec_driver_sql(query_insert_DimTime)
        return True

def load_dim_cliente(conn):
    """Carga solo clientes nuevos"""
    last_load_ts = get_last_load_timestamp(conn, "dw.DimCliente")
    clientes_stg = get_clientes_stg(conn, last_load_ts)
    
    if not clientes_stg:
        print("No hay nuevos clientes para cargar")
        return 0
    
    print(f"Cargando {len(clientes_stg)} nuevos clientes...")
    
    for cliente in clientes_stg:
        conn.execute(text(query_insert_dimCliente_dw), {
            'sourceSystem': cliente.sourceSystem, 
            'sourceKey': cliente.sourceCode,
            'Email': cliente.Email, 
            'Nombre': cliente.Nombre, 
            'Genero': cliente.Genero, 
            'Pais': cliente.Pais,
            'FechaCreacion': cliente.FechaCreacion
        })
    
    return len(clientes_stg)

def load_dim_producto(conn):
    """Carga productos - maneja la falta de load_ts en map_producto"""
    
    # Opción 1: Cargar solo productos nuevos (recomendado para producción)
    productos_stg = get_new_map_productos(conn)
    
    if not productos_stg:
        print("No hay nuevos productos para cargar")
        return 0
    
    print(f"Cargando {len(productos_stg)} nuevos productos...")
    
    loaded_count = 0
    for producto in productos_stg:
        # Doble verificación para evitar duplicados
        if not product_exists(conn, producto.SourceSystem, producto.SourceKey):
            conn.execute(text(query_insert_dimProducto_dw), {
                'SourceSystem': producto.SourceSystem, 
                'SourceKey': producto.SourceKey,
                'SKU': producto.SKU, 
                'Nombre': producto.Nombre, 
                'Categoria': producto.Categoria,
                'EsServicio': producto.EsServicio,
            })
            loaded_count += 1
    
    return loaded_count

def load_dim_producto_initial(conn):
    """Carga inicial de todos los productos (usar solo primera vez)"""
    productos_stg = get_map_productos(conn)
    
    if not productos_stg:
        print("No hay productos para cargar")
        return 0
    
    print(f"Cargando {len(productos_stg)} productos (carga inicial)...")
    
    loaded_count = 0
    for producto in productos_stg:
        # Solo insertar si no existe
        if not product_exists(conn, producto.SourceSystem, producto.SourceKey):
            conn.execute(text(query_insert_dimProducto_dw), {
                'SourceSystem': producto.SourceSystem, 
                'SourceKey': producto.SourceKey,
                'SKU': producto.SKU, 
                'Nombre': producto.Nombre, 
                'Categoria': producto.Categoria,
                'EsServicio': producto.EsServicio,
            })
            loaded_count += 1
    
    print(f"Se cargaron {loaded_count} nuevos productos de {len(productos_stg)} encontrados")
    return loaded_count

def load_fact_ventas(conn):
    """Carga solo ventas nuevas"""
    last_load_ts = get_last_load_timestamp(conn, "dw.FactVentas")
    
    # Verificar si hay nuevas ventas
    result = conn.execute(text(query_select_new_orders), 
                         {'last_load_ts': last_load_ts})
    new_records = result.fetchone()[0]
    
    if new_records == 0:
        print("No hay nuevas ventas para cargar")
        return 0
    
    print(f"Cargando {new_records} nuevas ventas...")
    conn.execute(text(query_insert_factVentas), 
                {'last_load_ts': last_load_ts})
    
    return new_records

''' -----------------------------------------------------------------------
            Funcion principal para cargar el DataWarehouse
    ----------------------------------------------------------------------- ''' 

def load_datawarehouse():
    try:
        with engine.begin() as conn:
            # Verificar si el proceso debe ejecutarse
            should_run, reason = should_run_process(conn)
            
            if not should_run:
                print(f"El proceso no se ejecutará: {reason}")
                return {
                    'executed': False,
                    'reason': reason,
                    'details': {
                        'dim_tiempo_updated': False,
                        'clientes_loaded': 0,
                        'productos_loaded': 0,
                        'ventas_loaded': 0
                    }
                }
            
            print("Iniciando carga del DataWarehouse")
            
            # Ejecutar las cargas
            load_dim_tiempo(conn)
            load_dim_cliente(conn)
            load_dim_producto(conn)  
            load_fact_ventas(conn)

            
            return "Carga del DataWarehouse completada exitosamente!"
            
    except Exception as e:
        print(f"Error durante la carga del DataWarehouse: {str(e)}")
        raise
