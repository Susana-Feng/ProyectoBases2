import pandas as pd
import pycountry

from bson import ObjectId
from sqlalchemy import text
from configs.connections import get_dw_engine, get_supabase_client
from datetime import datetime

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
            Funciones de preparacion de datos para staging de Supabase
    ----------------------------------------------------------------------- """

def find_sku():
    engine = get_dw_engine()
    result = pd.read_sql(query_select_map_producto_sku, engine)

    if result.empty:
        return "SKU0001"

    colname = result.columns[0]
    raw_sku = result[colname].iloc[0]

    # Si viene vacío o NULL
    if raw_sku is None or pd.isna(raw_sku) or raw_sku.strip() == "":
        return "SKU0001"

    sku = raw_sku.strip()

    # ----- Extraer parte numérica -----
    # SKU0001  -> número empieza en 3
    # SKU-0001 -> número empieza en 4
    if sku.startswith("SKU-"):
        parte_numerica = sku[4:]   # Desde después del guion
    else:
        parte_numerica = sku[3:]   # Desde después de "SKU"

    try:
        numero = int(parte_numerica)
    except Exception:
        raise ValueError(f"No se pudo extraer el número del SKU: '{sku}'")

    # ----- Construir siguiente SKU -----
    nuevo_num = numero + 1
    nuevo_sku = f"SKU{nuevo_num:04d}"

    return nuevo_sku

"""
Busca un SKU existente en stg.map_producto que coincida por nombre_norm y categoria_norm.
Devuelve el sku_oficial si existe; de lo contrario, devuelve string vacío "".
"""
def obtener_sku_existente(nombre_norm, categoria_norm):
    try:
        engine = get_dw_engine()

        result = pd.read_sql(
            query_select_map_producto_sku_exist,
            engine,
            params={
                "nombre_norm": nombre_norm,
                "categoria_norm": categoria_norm
            }
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
        print("⚠️  SKU vacío o None recibido")
        return False

    try:
        engine = get_dw_engine()

        query = text("""
            SELECT TOP 1 sku_oficial, nombre_norm, categoria_norm
            FROM stg.map_producto
            WHERE sku_oficial = :sku;
        """)

        # Ejecutar con pandas
        result = pd.read_sql(
            query,
            con=engine,
            params={"sku": sku}
        )

        # Si no hay coincidencias
        if result.empty:
            return False

        db_nombre = result.iloc[0]["nombre_norm"] or ""
        db_categoria = result.iloc[0]["categoria_norm"] or ""

        # Comparación exacta (puedo hacerla insensible a mayúsculas si quieres)
        return (db_nombre.lower() == nombre.lower()) and (db_categoria.lower() == categoria.lower())

    except Exception as e:
        print(f"Error validando SKU en stg_map_producto: {e}")
        return False

def insert_map_producto(codigo_original, sku_nueva, nombre, categoria):
    # SKU puede estar vacío, obtener uno existente si es así
    es_servicio = False
    if not sku_nueva:
        es_servicio = True
        sku_nueva = ""
        codigo_original = ""

    with engine.connect() as conn:
        result = conn.execute(
            text(query_insert_map_producto),
            {
                "source_system": "supabase",
                "source_code": codigo_original,
                "sku_oficial": sku_nueva,
                "nombre_norm": nombre,
                "categoria_norm": categoria,
                "es_servicio": es_servicio,  
            },
        )

        conn.commit()

def insert_orden_items_stg(orden_completa):
    total_items = len(orden_completa)
    procesados = 0
    errores = 0

    for i in orden_completa:
        procesados += 1

        # Mostrar progreso cada 100 items
        if procesados % 100 == 0 or procesados == total_items:
            print(
                f"\r  Procesados: {procesados}/{total_items} items (errores: {errores})...",
                end="",
                flush=True,
            )
        # Validar y convertir fecha
        fecha_raw = i.get("fecha")
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
            total_num = float(i.get("total", 0))
        except (ValueError, TypeError):
            errores += 1
            continue

        # Mapeo de ProductoID para obtener sku
        producto_id = i.get("producto_id")
        if not producto_id:
            errores += 1
            continue

        try:
            response = (
                supabase.table("producto")
                .select("sku")
                .eq("producto_id", producto_id)
                .limit(1)
                .execute()
            )

            # Si response.data es None, vacío o no contiene "sku", devolver ""
            sku = response.data[0].get("sku", "") if response.data else ""

        except Exception as e:
            sku = ""   # Si ocurre cualquier error, dejar sku vacío
            errores += 1
            continue

        with engine.connect() as conn:
            conn.execute(
                text(query_insert_orden_item_stg),
                {
                    "source_system": "supabase",
                    "source_key_orden": i.get("orden_id"),
                    "source_key_item": i.get("producto_id"),
                    "source_code_prod": sku or "Sin código",
                    "cliente_key": i.get("cliente_id"),
                    "fecha_raw": i.get("fecha"),
                    "canal_raw": i.get("canal"),
                    "moneda": i.get("moneda"),
                    "cantidad_raw": i.get("cantidad"),
                    "precio_unit_raw": i.get("precio_unitario"),
                    "total_raw": i.get("total"),
                    "fecha_dt": fecha_dt,
                    "cantidad_num": cantidad_num,
                    "precio_unit_num": precio_unit_num,
                    "total_num": total_num,
                },
            )
            conn.commit()

    # Nueva línea al finalizar
    print()
    if errores > 0:
        print(f"⚠️  Items procesados con {errores} errores saltados")

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

    except:
        pass

    return ""

def insert_clientes_stg(clientes):
    total_clientes = len(clientes)
    procesados = 0
    errores = 0

    for cliente in clientes:
        procesados += 1

        # Mostrar progreso cada 50 clientes
        if procesados % 50 == 0 or procesados == total_clientes:
            print(
                f"\r  Procesados: {procesados}/{total_clientes} clientes (errores: {errores})...",
                end="",
                flush=True,
            )
        source_code = str(cliente.get("cliente_id"))  # ObjectId → string

        # Validar y convertir fecha de creación
        fecha_creado_raw = cliente.get("fecha_registro")
        if fecha_creado_raw:
            try:
                # Si viene string ISO desde Supabase: "2025-10-31" o "2025-10-31T13:20:00"
                if isinstance(fecha_creado_raw, str):
                    fecha_creado_dt = datetime.fromisoformat(fecha_creado_raw).date()
                    fecha_creado_raw_str = fecha_creado_raw

                # Si por alguna razón viniera como datetime
                elif hasattr(fecha_creado_raw, "date"):
                    fecha_creado_dt = fecha_creado_raw.date()
                    fecha_creado_raw_str = str(fecha_creado_raw)

                else:
                    # Cualquier otro formato no esperado → error
                    fecha_creado_dt = None
                    fecha_creado_raw_str = "1900-01-01"

            except Exception:
                # Si la conversión falla
                fecha_creado_dt = None
                fecha_creado_raw_str = "1900-01-01"
        else:
            # Si no hay fecha, usar fecha por defecto
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
        if (pais_codigo != ""):
            pais = pais_codigo
        else:
            pais = pais_nombre

        try:
            with engine.connect() as conn:
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
                conn.commit()
        except Exception as e:
            errores += 1
            continue

    # Nueva línea al finalizar
    print()
    if errores > 0:
        print(f"⚠️  Clientes procesados con {errores} errores saltados")

def convertir_sku(sku: str) -> str:
    """
    Convierte SKU de formato 'SKU-0000' a 'SKU0000'.
    Si no contiene guion, lo devuelve igual.
    """
    if "-" in sku:
        return sku.replace("-", "")
    return sku

""" -----------------------------------------------------------------------
            Función principal de transformación de datos de Supabase
    ----------------------------------------------------------------------- """

def transform_supabase(productos, clientes, ordenes):
    """
    Transforma y carga datos de Supabase a staging.
    """
    try:
        print("[Supabase Transform] Iniciando transformación...")

        # 1. Transformar y cargar productos al mapa
        print(f"[Supabase Transform] Procesando {len(productos)} productos...")
        productos_procesados = 0
        for producto in productos:
            try:
                codigo_original = producto.get("sku")
                if codigo_original:
                    es_sku_oficial = validar_producto_en_stg(codigo_original, producto.get("nombre"), producto.get("categoria"))
                    if es_sku_oficial:
                        sku_nueva = convertir_sku(codigo_original)
                    else:
                        sku_existente = obtener_sku_existente(producto.get("nombre"), producto.get("categoria"))
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
            except Exception as e:
                print(f"⚠️  Error procesando producto {producto.get('_id')}: {e}")
                continue

        print(
            f"[Supabase Transform] Productos mapeados: {productos_procesados}/{len(productos)}"
        )

        # 2. Cargar items a staging
        print(f"[Supabase Transform] Cargando {len(ordenes)} items a staging...")
        insert_orden_items_stg(ordenes)

        # 3. Cargar clientes a staging
        print(f"[Supabase Transform] Procesando {len(clientes)} clientes...")
        insert_clientes_stg(clientes)

        print("[Supabase Transform] Transformación completada exitosamente")

    except Exception as e:
        print(f"❌ Error crítico en transform_supabase: {e}")
        import traceback

        traceback.print_exc()
        raise