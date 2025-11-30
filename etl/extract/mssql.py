"""
extract/mssql.py
Extracción de datos desde la base de datos transaccional DB_SALES en MS SQL Server.
"""

from sqlalchemy import text

from configs.connections import get_mssql_sales_engine

engine = get_mssql_sales_engine()


def extract_mssql():
    """
    Extrae datos de las tablas Cliente, Producto, Orden y OrdenDetalle
    de la base de datos DB_SALES en MS SQL Server.

    Returns:
        tuple: (clientes, productos, ordenes, orden_detalles)
    """

    query_clientes = """
        SELECT
            ClienteId,
            Nombre,
            Email,
            Genero,
            Pais,
            FechaRegistro
        FROM dbo.Cliente
        ORDER BY ClienteId
    """

    query_productos = """
        SELECT
            ProductoId,
            SKU,
            Nombre,
            Categoria
        FROM dbo.Producto
        ORDER BY ProductoId
    """

    query_ordenes = """
        SELECT
            OrdenId,
            ClienteId,
            Fecha,
            Canal,
            Moneda,
            Total
        FROM dbo.Orden
        ORDER BY OrdenId
    """

    query_orden_detalles = """
        SELECT
            OrdenDetalleId,
            OrdenId,
            ProductoId,
            Cantidad,
            PrecioUnit,
            DescuentoPct
        FROM dbo.OrdenDetalle
        ORDER BY OrdenDetalleId
    """

    with engine.connect() as conn:
        # Extraer clientes
        result_clientes = conn.execute(text(query_clientes))
        clientes = result_clientes.fetchall()

        # Extraer productos
        result_productos = conn.execute(text(query_productos))
        productos = result_productos.fetchall()

        # Extraer órdenes
        result_ordenes = conn.execute(text(query_ordenes))
        ordenes = result_ordenes.fetchall()

        # Extraer detalles de órdenes
        result_detalles = conn.execute(text(query_orden_detalles))
        orden_detalles = result_detalles.fetchall()

    print(
        f"    mssql: {len(clientes)} clients | {len(productos)} products | {len(ordenes)} orders | {len(orden_detalles)} items"
    )

    return clientes, productos, ordenes, orden_detalles
