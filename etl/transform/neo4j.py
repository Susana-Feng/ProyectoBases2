import pandas as pd
import pycountry

from sqlalchemy import text
from configs.connections import get_dw_engine, get_neo4j_driver
from datetime import datetime

engine = get_dw_engine()
driver = get_neo4j_driver()

""" -----------------------------------------------------------------------
            Queries de SQL para transformación de datos de Neo4j
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

# Para obtener el ultimo sku
query_select_map_producto_sku = """
    SELECT 
        'SKU' +
        RIGHT(
            '0000' + CAST(
                MAX(
                    CAST(
                        CASE 
                            WHEN SUBSTRING(sku_oficial, 4, 1) = '-' 
                                THEN SUBSTRING(sku_oficial, 5, LEN(sku_oficial))  -- SKU-0001
                            ELSE SUBSTRING(sku_oficial, 4, LEN(sku_oficial))      -- SKU0001
                        END
                    AS INT)
                ) 
            AS VARCHAR(10)
        ), 4
    ) AS UltimoSKU
    FROM stg.map_producto;
"""

# Para obtener sku de producto que coincida por nombre y categoria
query_select_map_producto_sku_exist = """
    SELECT TOP 1
        sku_oficial AS SKU
    FROM
        stg.map_producto AS target
    WHERE
        target.nombre_norm = :nombre_norm
        AND target.categoria_norm = :categoria_norm
    ORDER BY
        target.map_id DESC;
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
            Funciones de preparacion de datos para staging de Neo4j
    ----------------------------------------------------------------------- """


def find_sku():
    engine = get_dw_engine()
    result = pd.read_sql(query_select_map_producto_sku, engine)

    if result.empty:
        return "SKU-0001"

    colname = result.columns[0]
    raw_sku = result[colname].iloc[0]

    # Si viene vacío o NULL
    if raw_sku is None or pd.isna(raw_sku) or raw_sku.strip() == "":
        return "SKU-0001"

    sku = raw_sku.strip()

    # ----- Extraer parte numérica -----
    # SKU0001  -> número empieza en 3
    # SKU-0001 -> número empieza en 4
    if sku.startswith("SKU-"):
        parte_numerica = sku[4:]  # Desde después del guion
    else:
        parte_numerica = sku[3:]  # Desde después de "SKU"

    try:
        numero = int(parte_numerica)
    except Exception:
        raise ValueError(f"No se pudo extraer el número del SKU: '{sku}'")

    # ----- Construir siguiente SKU -----
    nuevo_num = numero + 1
    nuevo_sku = f"SKU-{nuevo_num:04d}"

    return nuevo_sku


"""
Busca un SKU existente en stg.map_producto que coincida por Nombre y Categoria.
Devuelve el SKU oficial si existe; de lo contrario, devuelve string vacío "".
"""


def obtener_sku_existente(nombre_norm, categoria_norm):
    try:
        engine = get_dw_engine()

        result = pd.read_sql(
            query_select_map_producto_sku_exist,
            engine,
            params={"nombre_norm": nombre_norm, "categoria_norm": categoria_norm},
        )

        if result.empty:
            return ""  # no hay coincidencia

        sku = result["SKU"].iloc[0]
        return sku

    except Exception:
        return ""  # fallback seguro


def validar_producto_en_stg(sku: str, nombre: str, categoria: str) -> bool:
    """
    Valida si un SKU existe en stg.map_producto y si coinciden Nombre y Categoria.
    Retorna True si coincide todo, False en caso contrario.
    """

    # Si sku viene vacío o None → inmediatamente False
    if not sku:
        return False

    try:
        engine = get_dw_engine()

        query = text("""
            SELECT TOP 1 sku_oficial, nombre_norm, categoria_norm
            FROM stg.map_producto
            WHERE sku_oficial = :sku;
        """)

        # Ejecutar con pandas
        result = pd.read_sql(query, con=engine, params={"sku": sku})

        # Si no hay coincidencias
        if result.empty:
            return False

        db_nombre = result.iloc[0]["nombre_norm"] or ""
        db_categoria = result.iloc[0]["categoria_norm"] or ""

        # Case-sensitive comparison
        return (db_nombre.lower() == nombre.lower()) and (
            db_categoria.lower() == categoria.lower()
        )

    except Exception:
        return False


def insert_map_producto(codigo_original, sku_nueva, nombre, categoria):
    # SKU puede estar vacío, obtener uno existente si es así
    if not sku_nueva:
        sku_nueva = find_sku()
    # Ensure source_code is never empty (must match source_code_prod in orden_items)
    if not codigo_original:
        codigo_original = "Sin código"

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_map_producto),
            {
                "source_system": "neo4j",
                "source_code": codigo_original,
                "sku_oficial": sku_nueva,
                "nombre_norm": nombre,
                "categoria_norm": categoria,
                "es_servicio": False,
            },
        )

        conn.commit()


def unir_relaciones_por_orden(rel_realizo, rel_contiente):
    """
    Une las relaciones REALIZO y CONTIENTE por el ID de la orden.

    rel_realizo: Lista de dicts con relaciones Cliente->Orden
    rel_contiente: Lista de dicts con relaciones Orden->Producto

    return: Lista de dicts combinados
    """

    # Índice rápido para buscar cliente-orden por ID de orden
    index_realizo = {}
    for rel in rel_realizo:
        orden_id = rel["to"]["id"]  # orden está en "to"
        index_realizo[orden_id] = rel

    resultado = []

    # Asociar cada Orden->Producto con su Cliente correspondiente
    for rel in rel_contiente:
        orden_id = rel["from"]["id"]  # orden está en "from"

        if orden_id not in index_realizo:
            # Skip products without associated client
            continue

        rel_cliente_orden = index_realizo[orden_id]

        combinado = {
            "cliente": rel_cliente_orden["from"],
            "orden": rel_cliente_orden["to"],
            "producto": rel["to"],
            "detalle": rel["properties"],
        }

        resultado.append(combinado)

    return resultado


def insert_orden_items_stg(orden_completa, clientes_count, productos_count):
    """Insert order items with progress display."""
    total_items = len(orden_completa)
    procesados = 0
    errores = 0

    for i in orden_completa:
        # ----------------------------------------------
        # 1. Extraer datos del registro
        # ----------------------------------------------
        try:
            cliente = i["cliente"]
            orden = i["orden"]
            producto = i["producto"]
            detalle = i["detalle"]
        except KeyError:
            errores += 1
            continue

        # -----------------------------
        # 2. Validar y convertir fecha
        # -----------------------------
        fecha_raw = orden.get("fecha")
        if fecha_raw:
            try:
                fecha_native = fecha_raw.to_native()
                fecha_dt = fecha_native.date()
                fecha_str = fecha_raw.isoformat()
            except Exception:
                errores += 1
                continue
        else:
            errores += 1
            continue

        # Validar cantidad
        try:
            cantidad_num = float(detalle.get("cantidad", 0))
            if cantidad_num <= 0:
                errores += 1
                continue
        except (ValueError, TypeError):
            errores += 1
            continue

        # Validar precio unitario y total
        try:
            precio_unit_num = float(detalle.get("precio_unit", 0))
            total_num = float(orden.get("total", 0))
        except (ValueError, TypeError):
            errores += 1
            continue

        # Mapeo de ProductoID para obtener sku
        producto_id = producto.get("id")
        sku = producto.get("sku")

        if not producto_id or not sku:
            errores += 1
            continue

        with engine.connect() as conn:
            conn.execute(
                text(query_insert_orden_item_stg),
                {
                    "source_system": "neo4j",
                    "source_key_orden": str(orden.get("id")),
                    "source_key_item": str(producto_id),
                    "source_code_prod": sku or "Sin código",
                    "cliente_key": str(cliente.get("id")),
                    "fecha_raw": fecha_str,
                    "canal_raw": orden.get("canal"),
                    "moneda": orden.get("moneda"),
                    "cantidad_raw": str(detalle.get("cantidad")),
                    "precio_unit_raw": str(detalle.get("precio_unit")),
                    "total_raw": str(orden.get("total")),
                    "fecha_dt": fecha_dt,
                    "cantidad_num": cantidad_num,
                    "precio_unit_num": precio_unit_num,
                    "total_num": total_num,
                },
            )
            conn.commit()

        procesados += 1
        if (procesados + errores) % 100 == 0 or (procesados + errores) == total_items:
            print(
                f"\r    neo4j: {clientes_count} clients | {productos_count} products | {procesados}/{total_items} items...",
                end="",
                flush=True,
            )

    return procesados, errores


def pais_a_codigo(pais_nombre):
    """
    Convierte el nombre de un país a su código ISO de 2 letras (ej: Costa Rica -> CR).
    Si no lo encuentra, devuelve "".
    """
    if not pais_nombre:
        return ""

    try:
        country = pycountry.countries.get(name=pais_nombre)
        if country:
            return country.alpha_2

        # Intento adicional: búsqueda más flexible
        for c in pycountry.countries:
            if pais_nombre.lower() in c.name.lower():
                return c.alpha_2

    except Exception:  # noqa: BLE001
        pass

    return ""


def insert_clientes_stg(clientes):
    """Insert clients with progress display."""
    total_clientes = len(clientes)
    procesados = 0
    errores = 0

    for cliente in clientes:
        source_code = str(cliente.get("id"))

        # Validar y convertir fecha de creación
        fecha_creado_dt = datetime.now().date()
        fecha_creado_raw_str = fecha_creado_dt.isoformat()

        # Validar género
        genero_raw = cliente.get("genero")
        if genero_raw == "M":
            genero_nuevo = "Masculino"
        elif genero_raw == "F":
            genero_nuevo = "Femenino"
        elif genero_raw == "Otro":
            genero_nuevo = "No especificado"
        elif genero_raw in ("Masculino", "Femenino"):
            genero_nuevo = genero_raw
        else:
            genero_nuevo = "No especificado"

        # Transformar nombre pais
        pais_nombre = cliente.get("pais")
        pais_codigo = pais_a_codigo(pais_nombre)
        if pais_codigo != "":
            pais = pais_codigo
        else:
            pais = pais_nombre

        try:
            with engine.connect() as conn:
                conn.execute(
                    text(query_insert_clientes_stg),
                    {
                        "source_system": "neo4j",
                        "source_code": source_code,
                        "cliente_email": "Sin correo",
                        "cliente_nombre": cliente.get("nombre", "Sin nombre"),
                        "genero_raw": genero_raw if genero_raw else "No especificado",
                        "pais_raw": pais if pais else "CR",
                        "fecha_creado_raw": fecha_creado_raw_str,
                        "fecha_creado_dt": fecha_creado_dt,
                        "genero_norm": genero_nuevo,
                    },
                )
                conn.commit()
            procesados += 1
        except Exception:
            errores += 1
            continue

        if (procesados + errores) % 50 == 0 or (procesados + errores) == total_clientes:
            print(
                f"\r    neo4j: {procesados}/{total_clientes} clients...",
                end="",
                flush=True,
            )

    return procesados, errores


def convertir_sku(sku: str) -> str:
    """
    Normaliza SKU al formato 'SKU-0000'.
    Si viene sin guion (SKU0000), lo convierte a SKU-0000.
    Si ya tiene guion, lo devuelve igual.
    """
    if not sku:
        return sku
    # Si ya tiene el guion, devolverlo tal cual
    if "-" in sku:
        return sku
    # Si viene sin guion (SKU0000), agregar el guion después de "SKU"
    if sku.upper().startswith("SKU") and len(sku) > 3:
        return f"SKU-{sku[3:]}"
    return sku


""" -----------------------------------------------------------------------
            Función principal de transformación de datos de Neo4j
    ----------------------------------------------------------------------- """


def transform_Neo4j(productos, clientes, rel_realizo, rel_contiene):
    """
    Transforma y carga datos de Neo4j a staging.
    """
    total_productos = len(productos)

    # 1. Process clients
    clientes_procesados, clientes_errores = insert_clientes_stg(clientes)

    # 2. Process products and create mapping table
    productos_procesados = 0
    productos_errores = 0
    for producto in productos:
        try:
            codigo_original = producto.get("sku")
            if codigo_original:
                es_sku_oficial = validar_producto_en_stg(
                    codigo_original,
                    producto.get("nombre"),
                    producto.get("categoria"),
                )
                if es_sku_oficial:
                    sku_nueva = convertir_sku(codigo_original)
                else:
                    sku_existente = obtener_sku_existente(
                        producto.get("nombre"), producto.get("categoria")
                    )
                    if sku_existente:
                        sku_nueva = sku_existente
                    else:
                        sku_nueva = find_sku()
            else:
                sku_nueva = ""
            nombre = producto.get("nombre")
            categoria = producto.get("categoria")

            insert_map_producto(codigo_original, sku_nueva, nombre, categoria)
            productos_procesados += 1
        except Exception:
            productos_errores += 1
            continue

        if (productos_procesados + productos_errores) % 50 == 0 or (
            productos_procesados + productos_errores
        ) == total_productos:
            print(
                f"\r    neo4j: {clientes_procesados} clients | {productos_procesados}/{total_productos} products...",
                end="",
                flush=True,
            )

    # 3. Load order items to staging
    ordenes = unir_relaciones_por_orden(rel_realizo, rel_contiene)
    items_procesados, items_errores = insert_orden_items_stg(
        ordenes, clientes_procesados, productos_procesados
    )

    # Final line
    output = f"\r    neo4j: {clientes_procesados} clients | {productos_procesados} products | {items_procesados} items"
    total_errores = clientes_errores + productos_errores + items_errores
    if total_errores > 0:
        output += f" | {total_errores} errors"
    print(output + " " * 20)  # Extra spaces to clear progress indicators
