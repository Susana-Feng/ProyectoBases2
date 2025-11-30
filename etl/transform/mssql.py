"""
transform/mssql.py
Transformación de datos de MS SQL Server DB_SALES para carga en staging del Data Warehouse.

Heterogeneidades de MS SQL Server:
- Género: 'Masculino', 'Femenino' (ya normalizado)
- Moneda: Siempre 'USD' (no requiere conversión)
- SKU: SKU oficial que será la clave canónica
- Fechas: DATETIME2 que se convierte a DATE

NOTA: Se utilizan sentencias MERGE para garantizar idempotencia del ETL.
      Si se ejecuta varias veces, no duplicará datos.
"""

from datetime import datetime

from sqlalchemy import text

from configs.connections import get_dw_engine

engine = get_dw_engine()

# -----------------------------------------------------------------------
#            Queries de SQL para transformación de datos de MS SQL Server
#            Usando MERGE para evitar duplicados (idempotente)
# -----------------------------------------------------------------------

query_insert_map_producto = """
    MERGE INTO stg.map_producto AS target
    USING (SELECT
        :source_system AS source_system,
        :source_code AS source_code,
        :sku_oficial AS sku_oficial,
        :nombre_norm AS nombre_norm,
        :categoria_norm AS categoria_norm,
        :es_servicio AS es_servicio
    ) AS source
    ON target.source_system = source.source_system
        AND target.source_code = source.source_code
    WHEN MATCHED THEN
        UPDATE SET
            sku_oficial = source.sku_oficial,
            nombre_norm = source.nombre_norm,
            categoria_norm = source.categoria_norm,
            es_servicio = source.es_servicio
    WHEN NOT MATCHED THEN
        INSERT (source_system, source_code, sku_oficial, nombre_norm, categoria_norm, es_servicio)
        VALUES (source.source_system, source.source_code, source.sku_oficial,
                source.nombre_norm, source.categoria_norm, source.es_servicio);
"""

query_insert_clientes_stg = """
    MERGE INTO stg.clientes AS target
    USING (SELECT
        :source_system AS source_system,
        :source_code AS source_code,
        :cliente_email AS cliente_email,
        :cliente_nombre AS cliente_nombre,
        :genero_raw AS genero_raw,
        :pais_raw AS pais_raw,
        :fecha_creado_raw AS fecha_creado_raw,
        :fecha_creado_dt AS fecha_creado_dt,
        :genero_norm AS genero_norm
    ) AS source
    ON target.source_system = source.source_system
        AND target.source_code = source.source_code
    WHEN MATCHED THEN
        UPDATE SET
            cliente_email = COALESCE(source.cliente_email, target.cliente_email),
            cliente_nombre = COALESCE(source.cliente_nombre, target.cliente_nombre),
            genero_raw = COALESCE(source.genero_raw, target.genero_raw),
            pais_raw = COALESCE(source.pais_raw, target.pais_raw),
            fecha_creado_raw = COALESCE(source.fecha_creado_raw, target.fecha_creado_raw),
            fecha_creado_dt = COALESCE(source.fecha_creado_dt, target.fecha_creado_dt),
            genero_norm = COALESCE(source.genero_norm, target.genero_norm)
    WHEN NOT MATCHED THEN
        INSERT (source_system, source_code, cliente_email, cliente_nombre, genero_raw,
                pais_raw, fecha_creado_raw, fecha_creado_dt, genero_norm)
        VALUES (source.source_system, source.source_code, source.cliente_email,
                source.cliente_nombre, source.genero_raw, source.pais_raw,
                COALESCE(source.fecha_creado_raw, '1900-01-01'),
                source.fecha_creado_dt, source.genero_norm);
"""

query_insert_orden_item_stg = """
    MERGE INTO stg.orden_items AS target
    USING (SELECT
        :source_system AS source_system,
        :source_key_orden AS source_key_orden,
        :source_key_item AS source_key_item,
        :source_code_prod AS source_code_prod,
        :cliente_key AS cliente_key,
        :fecha_raw AS fecha_raw,
        :canal_raw AS canal_raw,
        :moneda AS moneda,
        :cantidad_raw AS cantidad_raw,
        :precio_unit_raw AS precio_unit_raw,
        :total_raw AS total_raw,
        :fecha_dt AS fecha_dt,
        :cantidad_num AS cantidad_num,
        :precio_unit_num AS precio_unit_num,
        :total_num AS total_num
    ) AS source
    ON target.source_system = source.source_system
        AND target.source_key_orden = source.source_key_orden
        AND target.source_key_item = source.source_key_item
    WHEN NOT MATCHED THEN
        INSERT (source_system, source_key_orden, source_key_item, source_code_prod,
                cliente_key, fecha_raw, canal_raw, moneda, cantidad_raw, precio_unit_raw,
                total_raw, fecha_dt, cantidad_num, precio_unit_num, total_num)
        VALUES (source.source_system, source.source_key_orden, source.source_key_item,
                source.source_code_prod, source.cliente_key, source.fecha_raw, source.canal_raw,
                source.moneda, source.cantidad_raw, source.precio_unit_raw, source.total_raw,
                source.fecha_dt, source.cantidad_num, source.precio_unit_num, source.total_num);
"""

# -----------------------------------------------------------------------
#     Funciones de preparación de datos para staging de MS SQL Server
# -----------------------------------------------------------------------


def insert_map_producto(producto):
    """
    Inserta un producto en la tabla stg.map_producto.

    Args:
        producto: Row con datos del producto (ProductoId, SKU, Nombre, Categoria)
    """
    source_code = str(producto.ProductoId)
    sku_oficial = producto.SKU  # SKU oficial de MS SQL Server
    nombre = producto.Nombre
    categoria = producto.Categoria

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_map_producto),
            {
                "source_system": "mssql",
                "source_code": source_code,
                "sku_oficial": sku_oficial,
                "nombre_norm": nombre,
                "categoria_norm": categoria,
                "es_servicio": False,  # MS SQL Server solo tiene productos físicos
            },
        )
        conn.commit()


def insert_clientes_stg(cliente):
    """
    Inserta un cliente en la tabla stg.clientes aplicando normalización de género.

    Args:
        cliente: Row con datos del cliente (ClienteId, Nombre, Email, Genero, Pais, FechaRegistro)
    """
    source_code = str(cliente.ClienteId)
    genero_raw = cliente.Genero

    # Normalización de género (MS SQL Server ya usa 'Masculino'/'Femenino')
    # Validar y normalizar por si hay valores nulos o inesperados
    if genero_raw == "Masculino":
        genero_norm = "Masculino"
    elif genero_raw == "Femenino":
        genero_norm = "Femenino"
    else:
        genero_norm = "No especificado"

    # Convertir fecha a DATE si es datetime
    if isinstance(cliente.FechaRegistro, datetime):
        fecha_creado_dt = cliente.FechaRegistro.date()
    else:
        fecha_creado_dt = cliente.FechaRegistro

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_clientes_stg),
            {
                "source_system": "mssql",
                "source_code": source_code,
                "cliente_email": cliente.Email,
                "cliente_nombre": cliente.Nombre,
                "genero_raw": genero_raw,
                "pais_raw": cliente.Pais,
                "fecha_creado_raw": str(cliente.FechaRegistro),
                "fecha_creado_dt": fecha_creado_dt,
                "genero_norm": genero_norm,
            },
        )
        conn.commit()


def insert_orden_items_stg(orden, detalle, productos_dict):
    """
    Inserta un item de orden en la tabla stg.orden_items.

    Args:
        orden: Row con datos de la orden
        detalle: Row con datos del detalle de orden
        productos_dict: Diccionario {ProductoId: SKU} para mapeo rápido (no usado en source_code_prod)
    """
    # El source_code_prod debe coincidir con source_code en map_producto
    # Para MSSQL, ambos usan ProductoId como string
    source_code_prod = str(detalle.ProductoId)

    # Convertir fecha a DATE
    if isinstance(orden.Fecha, datetime):
        fecha_dt = orden.Fecha.date()
    else:
        fecha_dt = orden.Fecha

    # Normalizar canal (MS SQL Server usa: WEB, TIENDA, APP)
    canal_raw = orden.Canal.upper() if orden.Canal else "WEB"

    # Convertir valores numéricos
    cantidad_num = float(detalle.Cantidad)
    precio_unit_num = float(detalle.PrecioUnit)

    # Calcular total del item (cantidad * precio_unit)
    # Aplicar descuento si existe
    descuento_pct = (
        float(detalle.DescuentoPct) if detalle.DescuentoPct is not None else 0.0
    )
    total_item = cantidad_num * precio_unit_num * (1 - descuento_pct / 100.0)

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_orden_item_stg),
            {
                "source_system": "mssql",
                "source_key_orden": str(orden.OrdenId),
                "source_key_item": str(detalle.OrdenDetalleId),
                "source_code_prod": source_code_prod,
                "cliente_key": str(orden.ClienteId),
                "fecha_raw": str(orden.Fecha),
                "canal_raw": canal_raw,
                "moneda": orden.Moneda,  # Siempre USD en MS SQL Server
                "cantidad_raw": str(detalle.Cantidad),
                "precio_unit_raw": str(detalle.PrecioUnit),
                "total_raw": str(total_item),
                "fecha_dt": fecha_dt,
                "cantidad_num": cantidad_num,
                "precio_unit_num": precio_unit_num,
                "total_num": total_item,
            },
        )
        conn.commit()


# -----------------------------------------------------------------------
#         Función principal de transformación de datos de MS SQL Server
# -----------------------------------------------------------------------


def transform_mssql(clientes, productos, ordenes, orden_detalles):
    """
    Transforma y carga los datos de MS SQL Server en las tablas de staging.

    Args:
        clientes: Lista de clientes extraídos
        productos: Lista de productos extraídos
        ordenes: Lista de órdenes extraídas
        orden_detalles: Lista de detalles de órdenes extraídos
    """
    total_items = len(orden_detalles)

    # 1. Process clients
    for i, cliente in enumerate(clientes):
        insert_clientes_stg(cliente)
        if (i + 1) % 50 == 0 or i == len(clientes) - 1:
            print(
                f"\r    mssql: {i + 1}/{len(clientes)} clients...",
                end="",
                flush=True,
            )

    # 2. Process products and create mapping table
    productos_dict = {}
    for i, producto in enumerate(productos):
        insert_map_producto(producto)
        productos_dict[producto.ProductoId] = producto.SKU
        if (i + 1) % 50 == 0 or i == len(productos) - 1:
            print(
                f"\r    mssql: {len(clientes)} clients | {i + 1}/{len(productos)} products...",
                end="",
                flush=True,
            )

    # 3. Process orders and details
    ordenes_dict = {orden.OrdenId: orden for orden in ordenes}

    items_procesados = 0
    for detalle in orden_detalles:
        orden = ordenes_dict.get(detalle.OrdenId)
        if orden:
            insert_orden_items_stg(orden, detalle, productos_dict)
            items_procesados += 1
            if items_procesados % 100 == 0 or items_procesados == total_items:
                print(
                    f"\r    mssql: {len(clientes)} clients | {len(productos)} products | {items_procesados}/{total_items} items...",
                    end="",
                    flush=True,
                )

    # Final line (extra spaces to clear progress indicators like "15000/15030 items...")
    print(
        f"\r    mssql: {len(clientes)} clients | {len(productos)} products | {items_procesados} items"
        + " " * 20
    )
