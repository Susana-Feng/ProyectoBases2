import pandas as pd
from configs.connections import get_dw_engine
from sqlalchemy import text

engine = get_dw_engine()

''' -----------------------------------------------------------------------
            Queries de SQL para cargar el DataWarehouse
    ----------------------------------------------------------------------- ''' 

query_insert_DimTime = """
    DECLARE @FechaInicio DATE = '2022-01-01';
    DECLARE @FechaFin    DATE = CAST(GETDATE() AS DATE);  -- Fecha actual

    ;WITH Fechas AS (
        SELECT @FechaInicio AS Fecha
        UNION ALL
        SELECT DATEADD(DAY, 1, Fecha)
        FROM Fechas
        WHERE Fecha < @FechaFin
    )
    INSERT INTO dw.DimTiempo (
        TiempoID, Fecha, Anio, Mes, Dia
    )
    SELECT
        CONVERT(INT, FORMAT(Fecha, 'yyyyMMdd')) AS TiempoID,
        Fecha,
        YEAR(Fecha)  AS Anio,
        MONTH(Fecha) AS Mes,
        DAY(Fecha)   AS Dia
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
        FechaCreacionID
    )
    SELECT
        :sourceSystem,
        :sourceKey,
        :Email,
        :Nombre,
        :Genero,
        :Pais,
        TiempoID
    FROM dw.DimTiempo
    WHERE Fecha = :FechaCreacion;

"""

query_select_clientes_stg = """
    SELECT
        C.source_system AS sourceSystem
        ,C.source_code AS sourceCode
        ,C.cliente_email AS Email
        , C.cliente_nombre AS Nombre
        ,C.genero_norm AS Genero
        , C.pais_raw AS Pais
        , C.fecha_creado_dt AS  FechaCreacion
    FROM
        stg.clientes AS C
"""

query_select_map_producto = """
    SELECT
        P.source_system AS SourceSystem,
        P.source_code AS SourceKey,
        P.nombre_norm AS Nombre,
        P.categoria_norm AS Categoria,
        P.es_servicio AS EsServicio
    FROM
         stg.map_producto AS P
"""

query_insert_dimCliente_dw = """
    INSERT INTO dw.DimCliente (
        SourceSystem,
        SourceKey,
        Email,
        Nombre,
        Genero,
        Pais,
        FechaCreacionID
    )
    SELECT
        :sourceSystem,
        :sourceKey,
        :Email,
        :Nombre,
        :Genero,
        :Pais,
        TiempoID
    FROM dw.DimTiempo
    WHERE Fecha = :FechaCreacion;

"""

query_insert_dimProducto_dw = """
    INSERT INTO dw.DimProducto (
        SKU,
        Nombre,
        Categoria,
        EsServicio,
        SourceSystem,
        SourceKey
    )
    VALUES (
        :SKU,
        :Nombre,
        :Categoria,
        :EsServicio,
        :SourceSystem,
        :SourceKey)
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
        SourceKey)
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
        O.source_key_orden
    FROM
        dw.DimTiempo AS T
        ,stg.orden_items AS O
    INNER JOIN dw.DimCliente AS C
    ON O.cliente_key = C.SourceKey
    INNER JOIN dw.DimProducto AS P
    ON O.source_code_prod = P.SourceKey
    WHERE
        T.Fecha = O.fecha_dt
"""


''' -----------------------------------------------------------------------
            Funciones auxiliares para cargar el DataWarehouse
    ----------------------------------------------------------------------- ''' 


def get_clientes_stg():
    with engine.connect() as conn:
        result = conn.execute(text(query_select_clientes_stg))
        clientes_stg = result.fetchall()
    return clientes_stg


def get_map_productos():
    with engine.connect() as conn:
        result = conn.execute(text(query_select_map_producto))
        productos_stg = result.fetchall()
    return productos_stg


def load_dim_tiempo():

    # Cargar DimTiempo desde 2024-01-01 hasta 2025-12-31
    with engine.begin() as conn:
        conn.exec_driver_sql(query_insert_DimTime)


def load_dim_cliente():

    clientes_stg = get_clientes_stg()

    for cliente in clientes_stg:
        with engine.connect() as conn:
                conn.execute(text(query_insert_dimCliente_dw), {
                        'sourceSystem':cliente.sourceSystem, 
                        'sourceKey': cliente.sourceCode,
                        'Email': cliente.Email, 
                        'Nombre': cliente.Nombre, 
                        'Genero': cliente.Genero, 
                        'Pais': cliente.Pais,
                        'FechaCreacion': cliente.FechaCreacion
                    })
                conn.commit()


def load_dim_producto():

    productos_stg = get_map_productos()

    for producto in productos_stg:
        with engine.connect() as conn:
                conn.execute(text(query_insert_dimProducto_dw), {
                        'SourceSystem':producto.SourceSystem, 
                        'SourceKey': producto.SourceKey,
                        'SKU': producto.SourceKey, 
                        'Nombre': producto.Nombre, 
                        'Categoria': producto.Categoria,
                        'EsServicio': producto.EsServicio,
                    })
                conn.commit()


def load_fact_ventas():
    with engine.begin() as conn:
        conn.exec_driver_sql(query_insert_factVentas)    


''' -----------------------------------------------------------------------
            Funcion principal para cargar el DataWarehouse
    ----------------------------------------------------------------------- ''' 


def load_datawarehouse():
    load_dim_tiempo()
    load_dim_cliente()
    load_dim_producto()
    load_fact_ventas()