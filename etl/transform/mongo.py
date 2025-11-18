import pandas as pd
from bson import ObjectId
from sqlalchemy import text

from configs.connections import get_dw_engine, get_mongo_database

db = get_mongo_database()
products_collection = db["productos"]

engine = get_dw_engine()


""" -----------------------------------------------------------------------
            Queries de SQL para transformación de datos de MongoDB
    ----------------------------------------------------------------------- """

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

query_select_map_producto_sku = """
    SELECT TOP 1
        sku_oficial AS SKU
    FROM
        stg.map_producto
    ORDER BY
        map_id DESC
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

""" -----------------------------------------------------------------------
            Funciones de preparacion de datos para staging de MongoDB
    ----------------------------------------------------------------------- """


def find_sku():
    result = (pd.read_sql(query_select_map_producto_sku, engine))["SKU"].iloc[
        0
    ]  # convertir a dataframe y obtener valor de SKU
    sku = int(result.split("SKU")[1]) + 1  # obtener siguiente numero de SKU
    sku = "SKU" + str(sku).zfill(4)  # Cambiar formato a SKUxxxx

    return sku


def insert_map_producto(codigo_original, sku_nueva, nombre, categoria):
    # SKU puede estar vacío, obtener uno existente si es así
    if not sku_nueva:
        sku_nueva = find_sku()

    with engine.connect() as conn:
        result = conn.execute(
            text(query_insert_map_producto),
            {
                "source_system": "mongo",
                "source_code": codigo_original,
                "sku_oficial": sku_nueva,
                "nombre_norm": nombre,
                "categoria_norm": categoria,
                "es_servicio": False,  # Mongo solo tiene productos físicos
            },
        )

        conn.commit()


def flatten_items(orden, items_flat):
    id_orden = str(orden.get("_id"))  # ObjectId → string
    cliente_id = orden.get("cliente_id")
    fecha_orden = orden.get("fecha")
    canal = orden.get("canal")
    moneda = orden.get("moneda")
    total = orden.get("total")
    items = orden.get("items", [])
    metadatos = orden.get("metadatos", {})

    for i in items:  # estableciendo relación 1 a N de ordenes con items separados
        items_flat.append(
            {
                "orden_id": id_orden,
                "cliente_id": cliente_id,
                "fecha": fecha_orden,
                "canal": canal,
                "moneda": moneda,
                "total_orden": total,
                "producto_id": i.get("producto_id"),
                "cantidad": i.get("cantidad"),
                "precio_unitario": i.get("precio_unit"),
                "metadatos": metadatos,
            }
        )


def insert_orden_items_stg(items_flat):
    total_items = len(items_flat)
    procesados = 0
    errores = 0

    for i in items_flat:
        procesados += 1

        # Mostrar progreso cada 100 items
        if procesados % 100 == 0 or procesados == total_items:
            print(
                f"  Procesados: {procesados}/{total_items} items (errores: {errores})..."
            )
        # Validar y convertir fecha
        fecha_raw = i.get("fecha")
        if fecha_raw and hasattr(fecha_raw, "date"):
            fecha_dt = fecha_raw.date()
        else:
            errores += 1
            continue

        # Validar cantidad
        try:
            cantidad_num = float(i.get("cantidad", 0))
            if cantidad_num <= 0:
                errores += 1
                continue
        except (ValueError, TypeError):
            errores += 1
            continue

        # Validar precio unitario y total
        try:
            precio_unit_num = float(i.get("precio_unitario", 0))
            total_num = float(i.get("total_orden", 0))
        except (ValueError, TypeError):
            errores += 1
            continue

        # Mapeo de ProductoID para obtener codigo_mongo
        producto_id = i.get("producto_id")
        if not producto_id:
            errores += 1
            continue

        try:
            producto_obj = products_collection.find_one(
                {"_id": ObjectId(producto_id)}, {"codigo_mongo": 1}
            )
            codigo_mongo = producto_obj["codigo_mongo"] if producto_obj else None

            if not codigo_mongo:
                errores += 1
                continue
        except Exception as e:
            errores += 1
            continue

        with engine.connect() as conn:
            conn.execute(
                text(query_insert_orden_item_stg),
                {
                    "source_system": "mongo",
                    "source_key_orden": i.get("orden_id"),
                    "source_key_item": i.get("producto_id"),
                    "source_code_prod": codigo_mongo,
                    "cliente_key": i.get("cliente_id"),
                    "fecha_raw": i.get("fecha"),
                    "canal_raw": i.get("canal"),
                    "moneda": i.get("moneda"),
                    "cantidad_raw": i.get("cantidad"),
                    "precio_unit_raw": i.get("precio_unitario"),
                    "total_raw": i.get("total_orden"),
                    "fecha_dt": fecha_dt,
                    "cantidad_num": cantidad_num,
                    "precio_unit_num": precio_unit_num,
                    "total_num": total_num,
                },
            )
            conn.commit()

    if errores > 0:
        print(f"⚠️  Items procesados con {errores} errores saltados")


def insert_clientes_stg(clientes):
    total_clientes = len(clientes)
    procesados = 0
    errores = 0

    for cliente in clientes:
        procesados += 1

        # Mostrar progreso cada 50 clientes
        if procesados % 50 == 0 or procesados == total_clientes:
            print(
                f"  Procesados: {procesados}/{total_clientes} clientes (errores: {errores})..."
            )
        source_code = str(cliente.get("_id"))  # ObjectId → string

        # Validar y convertir fecha de creación
        fecha_creado_raw = cliente.get("creado")
        if fecha_creado_raw:
            if hasattr(fecha_creado_raw, "date"):
                fecha_creado_dt = fecha_creado_raw.date()
                fecha_creado_raw_str = str(fecha_creado_raw)
            else:
                fecha_creado_dt = None
                fecha_creado_raw_str = str(fecha_creado_raw)
        else:
            # Si no hay fecha, usar fecha por defecto
            fecha_creado_dt = None
            fecha_creado_raw_str = "1900-01-01"

        # Validar género
        genero_raw = cliente.get("genero")
        if genero_raw == "Otro":
            genero_nuevo = "No especificado"
        elif genero_raw in ("Masculino", "Femenino"):
            genero_nuevo = genero_raw
        else:
            genero_nuevo = "No especificado"

        try:
            with engine.connect() as conn:
                conn.execute(
                    text(query_insert_clientes_stg),
                    {
                        "source_system": "mongo",
                        "source_code": source_code,
                        "cliente_email": cliente.get("email"),
                        "cliente_nombre": cliente.get("nombre", "Sin nombre"),
                        "genero_raw": genero_raw if genero_raw else "No especificado",
                        "pais_raw": cliente.get("pais", "CR"),
                        "fecha_creado_raw": fecha_creado_raw_str,
                        "fecha_creado_dt": fecha_creado_dt,
                        "genero_norm": genero_nuevo,
                    },
                )
                conn.commit()
        except Exception as e:
            errores += 1
            continue

    if errores > 0:
        print(f"⚠️  Clientes procesados con {errores} errores saltados")


""" -----------------------------------------------------------------------
            Función principal de transformación de datos de MongoDB
    ----------------------------------------------------------------------- """


def transform_mongo(productos, clientes, ordenes):
    """
    Transforma y carga datos de MongoDB a staging.
    """
    try:
        print("[MongoDB Transform] Iniciando transformación...")

        # 1. Transformar y cargar productos al mapa
        print(f"[MongoDB Transform] Procesando {len(productos)} productos...")
        productos_procesados = 0
        for producto in productos:
            try:
                codigo_original = producto.get("codigo_mongo")
                sku_nueva = producto.get("equivalencias", {}).get("sku")
                nombre = producto.get("nombre")
                categoria = producto.get("categoria")

                insert_map_producto(codigo_original, sku_nueva, nombre, categoria)
                productos_procesados += 1
            except Exception as e:
                print(f"⚠️  Error procesando producto {producto.get('_id')}: {e}")
                continue

        print(
            f"[MongoDB Transform] Productos mapeados: {productos_procesados}/{len(productos)}"
        )

        # 2. Flatten items de órdenes
        print(f"[MongoDB Transform] Procesando {len(ordenes)} órdenes...")
        items_flat = []
        for orden in ordenes:
            try:
                flatten_items(orden, items_flat)  # 'normalizar' items en ordenes
            except Exception as e:
                print(f"⚠️  Error procesando orden {orden.get('_id')}: {e}")
                continue

        print(f"[MongoDB Transform] Items extraídos de órdenes: {len(items_flat)}")

        # 3. Cargar items a staging
        print(f"[MongoDB Transform] Cargando {len(items_flat)} items a staging...")
        insert_orden_items_stg(items_flat)

        # 4. Cargar clientes a staging
        print(f"[MongoDB Transform] Procesando {len(clientes)} clientes...")
        insert_clientes_stg(clientes)

        print("[MongoDB Transform] Transformación completada exitosamente")

    except Exception as e:
        print(f"❌ Error crítico en transform_mongo: {e}")
        import traceback

        traceback.print_exc()
        raise
