"""
extract/mysql.py
Extracción de datos desde la base de datos transaccional DB_SALES en MySQL.

Heterogeneidades de MySQL:
- Género: ENUM('M','F','X')
- Moneda: Puede ser 'USD' o 'CRC'
- Canal: libre (no controlado)
- Fechas: Almacenadas como VARCHAR (YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)
- Montos: Almacenados como VARCHAR, formatos '1200.50' o '1,200.50'
- Código Producto: 'codigo_alt' código alterno (no coincide con SKU oficial)
"""

from sqlalchemy import text

from configs.connections import get_mysql_engine

engine = get_mysql_engine()


def extract_mysql():
    """
    Extrae datos de las tablas Cliente, Producto, Orden y OrdenDetalle
    de la base de datos DB_SALES en MySQL.

    Returns:
        tuple: (clientes, productos, ordenes, orden_detalles)
    """

    query_clientes = """
        SELECT
            id,
            nombre,
            correo,
            genero,
            pais,
            created_at
        FROM Cliente
        ORDER BY id
    """

    query_productos = """
        SELECT
            id,
            codigo_alt,
            nombre,
            categoria
        FROM Producto
        ORDER BY id
    """

    query_ordenes = """
        SELECT
            id,
            cliente_id,
            fecha,
            canal,
            moneda,
            total
        FROM Orden
        ORDER BY id
    """

    query_orden_detalles = """
        SELECT
            id,
            orden_id,
            producto_id,
            cantidad,
            precio_unit
        FROM OrdenDetalle
        ORDER BY id
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
        f"    mysql: {len(clientes)} clients | {len(productos)} products | {len(ordenes)} orders | {len(orden_detalles)} items"
    )

    return clientes, productos, ordenes, orden_detalles
