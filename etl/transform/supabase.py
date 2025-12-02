import pandas as pd
import pycountry
from typing import TYPE_CHECKING

from sqlalchemy import text
from configs.connections import get_dw_engine, get_supabase_client
from datetime import datetime

if TYPE_CHECKING:
    from equivalences import EquivalenceMap

engine = get_dw_engine()
supabase = get_supabase_client()

""" -----------------------------------------------------------------------
            Queries de SQL para transformación de datos de Supabase
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

# Query to find SKU by name and category (case-insensitive, priority to mssql)
query_select_map_producto_sku_exist = """
    SELECT TOP 1
        sku_oficial AS SKU
    FROM
        stg.map_producto AS target
    WHERE
        LOWER(target.nombre_norm) = LOWER(:nombre_norm)
        AND LOWER(target.categoria_norm) = LOWER(:categoria_norm)
        AND target.sku_oficial IS NOT NULL
        AND target.sku_oficial != ''
    ORDER BY
        CASE target.source_system
            WHEN 'mssql' THEN 1
            ELSE 2
        END,
        target.map_id DESC;
"""

# Query to verify if a SKU exists in map_producto
query_find_sku_exists = """
    SELECT TOP 1 sku_oficial
    FROM stg.map_producto
    WHERE sku_oficial = :sku
      AND sku_oficial IS NOT NULL
      AND sku_oficial != ''
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
            Funciones de preparacion de datos para staging de Supabase
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
Busca un SKU existente en stg.map_producto que coincida por nombre_norm y categoria_norm.
Devuelve el sku_oficial si existe; de lo contrario, devuelve string vacío "".
"""


def obtener_sku_existente(nombre_norm, categoria_norm):
    """
    Find existing SKU by name+category match.
    Prioritizes MSSQL (canonical source) over other sources.
    """
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


def verificar_sku_existe(sku: str) -> str | None:
    """
    Verify if a SKU already exists in map_producto.
    Returns the SKU if found, None otherwise.
    """
    if not sku:
        return None
    try:
        engine = get_dw_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query_find_sku_exists), {"sku": sku})
            row = result.fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return None


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

    except Exception as e:
        print(f"Error validando SKU en stg_map_producto: {e}")
        return False


def insert_map_producto(
    producto_id,
    codigo_original,
    sku_nueva,
    nombre,
    categoria,
    eq_map: "EquivalenceMap" = None,
):
    """
    Inserta producto en map_producto.

    Uses the equivalence map (built from ALL sources) to get the correct SKU.

    Args:
        producto_id: UUID del producto en Supabase (usado como fallback source_code)
        codigo_original: SKU original de Supabase (puede ser None/vacío)
        sku_nueva: SKU procesado (puede estar vacío)
        nombre: Nombre del producto
        categoria: Categoría del producto
        eq_map: Mapa de equivalencias de productos
    """
    es_servicio = False
    sku_oficial = None

    # Use equivalence map (preferred - has info from all sources)
    if eq_map:
        sku_oficial = eq_map.get_sku_by_name(nombre, categoria)
        if sku_oficial:
            # Check if it's a service from the equivalence map
            eq = eq_map.get_equivalence(nombre, categoria)
            if eq and eq.es_servicio:
                es_servicio = True

    # Fallback: Si tiene SKU, verificar formato y existencia
    if not sku_oficial and sku_nueva:
        existing = verificar_sku_existe(sku_nueva)
        if existing:
            sku_oficial = existing
        elif sku_nueva.startswith("SKU-"):
            sku_oficial = sku_nueva

    # Fallback: Buscar por nombre+categoria en DB
    if not sku_oficial:
        sku_existente = obtener_sku_existente(nombre, categoria)
        if sku_existente:
            sku_oficial = sku_existente

    # Last resort: Generate new SKU
    if not sku_oficial:
        es_servicio = not bool(codigo_original)  # Service if no original SKU
        sku_oficial = find_sku()

    # Use producto_id as source_code if no SKU original
    if codigo_original:
        source_code = codigo_original
    else:
        source_code = str(producto_id) if producto_id else "Sin código"

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_map_producto),
            {
                "source_system": "supabase",
                "source_code": source_code,
                "sku_oficial": sku_oficial,
                "nombre_norm": nombre,
                "categoria_norm": categoria,
                "es_servicio": es_servicio,
            },
        )

        conn.commit()


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
            Función principal de transformación de datos de Supabase
    ----------------------------------------------------------------------- """


def transform_supabase(
    clientes, productos, ordenes, orden_detalles, eq_map: "EquivalenceMap" = None
):
    """
    Transforma y carga datos de Supabase a staging.

    Args:
        clientes: Lista de clientes extraídos
        productos: Lista de productos extraídos
        ordenes: Lista de órdenes extraídas
        orden_detalles: Lista de detalles de órdenes extraídos
        eq_map: Mapa de equivalencias de productos (construido previamente)
    """
    total_productos = len(productos)

    # 1. Load clients to staging
    clientes_procesados, clientes_errores = insert_clientes_stg_with_progress(
        clientes, 0, 0
    )

    # 2. Transform and load products to mapping table - using equivalence map
    productos_dict = {}
    productos_procesados = 0
    productos_errores = 0
    for producto in productos:
        try:
            codigo_original = producto.get("sku")
            producto_id = producto.get("producto_id")
            nombre = producto.get("nombre")
            categoria = producto.get("categoria")

            # Store in dict for later lookup
            productos_dict[producto_id] = codigo_original or str(producto_id)

            # Normalize SKU if provided
            sku_normalizado = convertir_sku(codigo_original) if codigo_original else ""

            # Use equivalence map for SKU resolution
            insert_map_producto(
                producto_id, codigo_original, sku_normalizado, nombre, categoria, eq_map
            )
            productos_procesados += 1
        except Exception:
            productos_errores += 1
            continue

        if (productos_procesados + productos_errores) % 50 == 0 or (
            productos_procesados + productos_errores
        ) == total_productos:
            print(
                f"\r    supab: {clientes_procesados} clients | {productos_procesados}/{total_productos} products...",
                end="",
                flush=True,
            )

    # 3. Build ordenes_dict for efficient lookup (join orders with details)
    ordenes_dict = {orden.get("orden_id"): orden for orden in ordenes}

    # 4. Load order items to staging
    items_procesados, items_errores = insert_orden_items_stg_with_progress(
        orden_detalles,
        ordenes_dict,
        productos_dict,
        clientes_procesados,
        productos_procesados,
    )

    # Final line
    output = f"\r    supab: {clientes_procesados} clients | {productos_procesados} products | {items_procesados} items"
    total_errores = productos_errores + items_errores + clientes_errores
    if total_errores > 0:
        output += f" | {total_errores} errors"
    print(output + " " * 20)  # Extra spaces to clear progress indicators


def insert_orden_items_stg_with_progress(
    orden_detalles, ordenes_dict, productos_dict, clientes_count, productos_count
):
    """Insert order items with progress display.
    OPTIMIZED: Uses single connection and batch commits.

    Args:
        orden_detalles: List of order detail records
        ordenes_dict: Dict mapping orden_id to orden record
        productos_dict: Dict mapping producto_id to sku
        clientes_count: Number of processed clients (for progress display)
        productos_count: Number of processed products (for progress display)
    """
    total_items = len(orden_detalles)
    procesados = 0
    errores = 0
    BATCH_SIZE = 500

    with engine.connect() as conn:
        for detalle in orden_detalles:
            # Get the order for this detail
            orden_id = detalle.get("orden_id")
            orden = ordenes_dict.get(orden_id)
            if not orden:
                errores += 1
                continue

            # Validar y convertir fecha
            fecha_raw = orden.get("fecha")
            if fecha_raw:
                try:
                    fecha_dt = datetime.fromisoformat(fecha_raw).date()
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

            # Validar precio unitario
            try:
                precio_unit_num = float(detalle.get("precio_unit", 0))
            except (ValueError, TypeError):
                errores += 1
                continue

            # Get total from order
            try:
                total_num = float(orden.get("total", 0))
            except (ValueError, TypeError):
                total_num = 0.0

            # Get SKU from productos_dict
            producto_id = detalle.get("producto_id")
            if not producto_id:
                errores += 1
                continue
            sku = productos_dict.get(producto_id, "")

            conn.execute(
                text(query_insert_orden_item_stg),
                {
                    "source_system": "supabase",
                    "source_key_orden": str(orden_id),
                    "source_key_item": str(detalle.get("orden_detalle_id")),
                    "source_code_prod": sku or "Sin código",
                    "cliente_key": str(orden.get("cliente_id")),
                    "fecha_raw": str(fecha_raw),
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

            procesados += 1
            if procesados % BATCH_SIZE == 0:
                conn.commit()
                print(
                    f"\r    supab: {clientes_count} clients | {productos_count} products | {procesados}/{total_items} items...",
                    end="",
                    flush=True,
                )

        conn.commit()  # Final commit

    return procesados, errores


def insert_clientes_stg_with_progress(clientes, productos_count, items_count):
    """Insert clients with progress display.
    OPTIMIZED: Uses single connection and batch commits."""
    total_clientes = len(clientes)
    procesados = 0
    errores = 0
    BATCH_SIZE = 500

    with engine.connect() as conn:
        for cliente in clientes:
            source_code = str(cliente.get("cliente_id"))

            # Validar y convertir fecha de creación
            fecha_creado_raw = cliente.get("fecha_registro")
            if fecha_creado_raw:
                try:
                    if isinstance(fecha_creado_raw, str):
                        fecha_creado_dt = datetime.fromisoformat(
                            fecha_creado_raw
                        ).date()
                        fecha_creado_raw_str = fecha_creado_raw
                    elif hasattr(fecha_creado_raw, "date"):
                        fecha_creado_dt = fecha_creado_raw.date()
                        fecha_creado_raw_str = str(fecha_creado_raw)
                    else:
                        fecha_creado_dt = None
                        fecha_creado_raw_str = "1900-01-01"
                except Exception:
                    fecha_creado_dt = None
                    fecha_creado_raw_str = "1900-01-01"
            else:
                fecha_creado_dt = None
                fecha_creado_raw_str = "1900-01-01"

            # Validar género
            genero_raw = cliente.get("genero")
            if genero_raw == "M":
                genero_nuevo = "Masculino"
            elif genero_raw == "F":
                genero_nuevo = "Femenino"
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
                conn.execute(
                    text(query_insert_clientes_stg),
                    {
                        "source_system": "supabase",
                        "source_code": source_code,
                        "cliente_email": cliente.get("email"),
                        "cliente_nombre": cliente.get("nombre", "Sin nombre"),
                        "genero_raw": genero_raw if genero_raw else "No especificado",
                        "pais_raw": pais if pais else "CR",
                        "fecha_creado_raw": fecha_creado_raw_str,
                        "fecha_creado_dt": fecha_creado_dt,
                        "genero_norm": genero_nuevo,
                    },
                )
                procesados += 1
                if procesados % BATCH_SIZE == 0:
                    conn.commit()
                    print(
                        f"\r    supab: {procesados}/{total_clientes} clients...",
                        end="",
                        flush=True,
                    )
            except Exception:
                errores += 1
                continue

        conn.commit()  # Final commit

    return procesados, errores
