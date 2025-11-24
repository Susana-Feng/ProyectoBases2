"""
transform/mssql.py
Transformación de datos de MS SQL Server DB_SALES para carga en staging del Data Warehouse.

Heterogeneidades de MS SQL Server:
- Género: 'Masculino', 'Femenino' (ya normalizado)
- Moneda: Siempre 'USD' (no requiere conversión)
- SKU: SKU oficial que será la clave canónica
- Fechas: DATETIME2 que se convierte a DATE
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import text

from configs.connections import get_dw_engine

engine = get_dw_engine()

# -----------------------------------------------------------------------
#            Queries de SQL para transformación de datos de MS SQL Server
# -----------------------------------------------------------------------

query_insert_map_producto = """
    INSERT INTO stg.map_producto(
        source_system,
        source_code,
        sku_oficial,
        nombre_norm,
        categoria_norm,
        es_servicio )
    VALUES (
        :source_system,
        :source_code,
        :sku_oficial,
        :nombre_norm,
        :categoria_norm,
        :es_servicio );
"""

query_insert_clientes_stg = """
    INSERT INTO stg.clientes(
        source_system,
        source_code,
        cliente_email,
        cliente_nombre,
        genero_raw,
        pais_raw,
        fecha_creado_raw,
        fecha_creado_dt,
        genero_norm )
    VALUES (
        :source_system,
        :source_code,
        :cliente_email,
        :cliente_nombre,
        :genero_raw,
        :pais_raw,
        :fecha_creado_raw,
        :fecha_creado_dt,
        :genero_norm );
"""

query_insert_orden_item_stg = """
    INSERT INTO stg.orden_items(
        source_system,
        source_key_orden,
        source_key_item,
        source_code_prod,
        cliente_key,
        fecha_raw,
        canal_raw,
        moneda,
        cantidad_raw,
        precio_unit_raw,
        total_raw,
        fecha_dt,
        cantidad_num,
        precio_unit_num,
        total_num )
    VALUES (
        :source_system,
        :source_key_orden,
        :source_key_item,
        :source_code_prod,
        :cliente_key,
        :fecha_raw,
        :canal_raw,
        :moneda,
        :cantidad_raw,
        :precio_unit_raw,
        :total_raw,
        :fecha_dt,
        :cantidad_num,
        :precio_unit_num,
        :total_num )
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
        productos_dict: Diccionario {ProductoId: SKU} para mapeo rápido
    """
    # Obtener SKU del producto
    sku_producto = productos_dict.get(detalle.ProductoId, f"PROD-{detalle.ProductoId}")

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
                "source_code_prod": sku_producto,
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
    print("[MSSQL Transform] Iniciando transformación...")

    # 1. Procesar productos y crear tabla de mapeo
    print(f"[MSSQL Transform] Procesando {len(productos)} productos...")
    productos_dict = {}
    for producto in productos:
        insert_map_producto(producto)
        productos_dict[producto.ProductoId] = producto.SKU

    # 2. Procesar clientes
    print(f"[MSSQL Transform] Procesando {len(clientes)} clientes...")
    for cliente in clientes:
        insert_clientes_stg(cliente)

    # 3. Procesar órdenes y detalles
    # Crear diccionario de órdenes para acceso rápido
    print(f"[MSSQL Transform] Procesando {len(ordenes)} órdenes...")
    ordenes_dict = {orden.OrdenId: orden for orden in ordenes}

    # Procesar cada detalle de orden
    print(f"[MSSQL Transform] Procesando {len(orden_detalles)} detalles de órdenes...")
    items_procesados = 0
    for detalle in orden_detalles:
        orden = ordenes_dict.get(detalle.OrdenId)
        if orden:
            insert_orden_items_stg(orden, detalle, productos_dict)
            items_procesados += 1

            # Mostrar progreso cada 100 items
            if items_procesados % 100 == 0:
                print(
                    f"\r  Procesados: {items_procesados}/{len(orden_detalles)} items...",
                    end="",
                    flush=True,
                )

    # Nueva línea al finalizar
    print()
    print(f"[MSSQL Transform] Transformación completada:")
    print(f"  - Productos mapeados: {len(productos)}")
    print(f"  - Clientes procesados: {len(clientes)}")
    print(f"  - Items de órdenes procesados: {items_procesados}")
