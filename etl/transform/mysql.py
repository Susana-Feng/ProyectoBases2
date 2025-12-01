"""
transform/mysql.py
Transformación de datos de MySQL DB_SALES para carga en staging del Data Warehouse.

Heterogeneidades de MySQL:
- Género: ENUM('M','F','X') → Normalizar a 'Masculino', 'Femenino', 'No especificado'
- Moneda: Puede ser 'USD' o 'CRC' (requiere conversión a USD si es CRC)
- Canal: libre (no controlado) → Normalizar a valores estándar
- Fechas: VARCHAR 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS' → Parsear a DATE
- Montos: VARCHAR con formatos '1200.50' o '1,200.50' → Parsear a DECIMAL
- Código Producto: 'codigo_alt' → Mapear a SKU oficial

NOTA: Se utilizan sentencias MERGE para garantizar idempotencia del ETL.
      Si se ejecuta varias veces, no duplicará datos.
"""

from datetime import datetime
import re

from sqlalchemy import text

from configs.connections import get_dw_engine

engine = get_dw_engine()

# -----------------------------------------------------------------------
#            Queries de SQL para transformación de datos de MySQL
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

# Query para obtener el siguiente SKU disponible
query_select_max_sku = """
    SELECT 
        'SKU-' +
        RIGHT('0000' + CAST(
            COALESCE(MAX(CAST(
                CASE 
                    WHEN SUBSTRING(sku_oficial, 4, 1) = '-' 
                        THEN SUBSTRING(sku_oficial, 5, LEN(sku_oficial))  -- SKU-0001
                    ELSE SUBSTRING(sku_oficial, 4, LEN(sku_oficial))      -- SKU0001
                END
            AS INT)), 0) + 1
        AS VARCHAR(10)), 4) AS NextSKU
    FROM stg.map_producto
    WHERE sku_oficial LIKE 'SKU%';
"""

# Query para buscar SKU por codigo_alt
query_find_sku_by_codigo_alt = """
    SELECT TOP 1 sku_oficial 
    FROM stg.map_producto 
    WHERE source_system = 'mssql' 
        AND source_code IN (
            SELECT CAST(p.ProductoId AS NVARCHAR(128))
            FROM DB_SALES.dbo.Producto p
            WHERE p.SKU IN (
                SELECT mp2.sku_oficial 
                FROM stg.map_producto mp2 
                WHERE mp2.source_system = 'mysql' 
                    AND mp2.source_code = :codigo_alt
            )
        );
"""

# -----------------------------------------------------------------------
#     Funciones auxiliares para limpieza de datos de MySQL
# -----------------------------------------------------------------------


def normalizar_genero(genero_raw):
    """
    Normaliza el género de MySQL (M/F/X) al formato estándar del DW.

    Args:
        genero_raw: Valor original del género

    Returns:
        str: 'Masculino', 'Femenino' o 'No especificado'
    """
    if genero_raw is None:
        return "No especificado"

    genero_upper = str(genero_raw).upper().strip()

    if genero_upper == "M":
        return "Masculino"
    elif genero_upper == "F":
        return "Femenino"
    elif genero_upper in ("X", "OTRO", "OTHER"):
        return "No especificado"
    else:
        return "No especificado"


def normalizar_canal(canal_raw):
    """
    Normaliza el canal de venta al formato estándar del DW.
    MySQL no tiene restricción en el canal, puede venir cualquier valor.

    Args:
        canal_raw: Valor original del canal

    Returns:
        str: Canal normalizado
    """
    if canal_raw is None:
        return "WEB"

    canal_upper = str(canal_raw).upper().strip()

    # Mapeo de canales conocidos
    canal_map = {
        "WEB": "WEB",
        "TIENDA": "TIENDA",
        "APP": "APP",
        "PARTNER": "PARTNER",
        "ONLINE": "WEB",
        "STORE": "TIENDA",
        "MOVIL": "APP",
        "MOBILE": "APP",
    }

    return canal_map.get(canal_upper, canal_upper)


def parsear_fecha(fecha_str):
    """
    Parsea una fecha en formato VARCHAR a objeto date.
    MySQL almacena fechas como 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS'

    Args:
        fecha_str: String con la fecha

    Returns:
        date: Objeto date o None si no se puede parsear
    """
    if fecha_str is None:
        return None

    fecha_str = str(fecha_str).strip()

    # Intentar diferentes formatos
    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]

    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue

    return None


def parsear_monto(monto_str):
    """
    Parsea un monto en formato VARCHAR a float.
    MySQL almacena montos como '1200.50' o '1,200.50'

    Args:
        monto_str: String con el monto

    Returns:
        float: Monto como número o 0.0 si no se puede parsear
    """
    if monto_str is None:
        return 0.0

    monto_str = str(monto_str).strip()

    # Remover caracteres no numéricos excepto punto y coma
    # Detectar si usa coma como separador decimal (europeo) o como miles

    # Si tiene punto y coma, asumir coma = miles, punto = decimal
    if "," in monto_str and "." in monto_str:
        # Formato 1,200.50 (coma miles, punto decimal)
        monto_str = monto_str.replace(",", "")
    elif "," in monto_str:
        # Detectar si la coma es decimal o miles
        # Si hay 3 dígitos después de la coma, es separador de miles
        # Si hay 1-2 dígitos después de la coma, es decimal
        partes = monto_str.split(",")
        if len(partes) == 2 and len(partes[1]) <= 2:
            # Coma como decimal (formato europeo 1200,50)
            monto_str = monto_str.replace(",", ".")
        else:
            # Coma como miles (formato 1,200)
            monto_str = monto_str.replace(",", "")

    try:
        return float(monto_str)
    except ValueError:
        # Limpiar cualquier caracter no numérico
        monto_limpio = re.sub(r"[^\d.]", "", monto_str)
        try:
            return float(monto_limpio)
        except ValueError:
            return 0.0


def get_next_sku():
    """
    Obtiene el siguiente SKU disponible de la secuencia.

    Returns:
        str: SKU en formato 'SKU-xxxx'
    """
    with engine.connect() as conn:
        result = conn.execute(text(query_select_max_sku))
        row = result.fetchone()
        if row and row[0]:
            return row[0]
        return "SKU-0001"


# -----------------------------------------------------------------------
#     Funciones de preparación de datos para staging de MySQL
# -----------------------------------------------------------------------


def insert_map_producto(producto, sku_mapping):
    """
    Inserta un producto en la tabla stg.map_producto.
    Para MySQL, el source_code es el codigo_alt ya que es lo que identifica
    de manera única al producto y es lo que se referencia en OrdenDetalle.

    Args:
        producto: Row con datos del producto (id, codigo_alt, nombre, categoria)
        sku_mapping: Dict para rastrear SKUs asignados

    Returns:
        str: SKU asignado al producto
    """
    # Usamos codigo_alt como source_code porque es lo que se referencia en las órdenes
    source_code = producto.codigo_alt
    codigo_alt = producto.codigo_alt
    nombre = producto.nombre
    categoria = producto.categoria

    # Generar un nuevo SKU para este producto de MySQL
    if codigo_alt in sku_mapping:
        sku_oficial = sku_mapping[codigo_alt]
    else:
        sku_oficial = get_next_sku()
        sku_mapping[codigo_alt] = sku_oficial

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_map_producto),
            {
                "source_system": "mysql",
                "source_code": source_code,
                "sku_oficial": sku_oficial,
                "nombre_norm": nombre,
                "categoria_norm": categoria,
                "es_servicio": False,  # MySQL solo tiene productos físicos
            },
        )
        conn.commit()

    return sku_oficial


def insert_clientes_stg(cliente):
    """
    Inserta un cliente en la tabla stg.clientes aplicando normalización.

    Args:
        cliente: Row con datos del cliente (id, nombre, correo, genero, pais, created_at)
    """
    source_code = str(cliente.id)
    genero_raw = cliente.genero

    # Normalización de género (MySQL usa M/F/X)
    genero_norm = normalizar_genero(genero_raw)

    # Parsear fecha de creación (viene como VARCHAR en MySQL)
    fecha_creado_raw = cliente.created_at
    fecha_creado_dt = parsear_fecha(fecha_creado_raw)

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_clientes_stg),
            {
                "source_system": "mysql",
                "source_code": source_code,
                "cliente_email": cliente.correo,
                "cliente_nombre": cliente.nombre,
                "genero_raw": genero_raw,
                "pais_raw": cliente.pais,
                "fecha_creado_raw": str(fecha_creado_raw)
                if fecha_creado_raw
                else "1900-01-01",
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
        productos_dict: Diccionario {producto_id: codigo_alt} para mapeo rápido
    """
    # Obtener codigo_alt del producto
    codigo_alt = productos_dict.get(detalle.producto_id, f"PROD-{detalle.producto_id}")

    # Parsear fecha (viene como VARCHAR en MySQL)
    fecha_raw = orden.fecha
    fecha_dt = parsear_fecha(fecha_raw)

    if fecha_dt is None:
        # Si no se puede parsear la fecha, usar fecha por defecto
        fecha_dt = datetime.now().date()

    # Normalizar canal
    canal_raw = normalizar_canal(orden.canal)

    # Parsear montos (vienen como VARCHAR en MySQL)
    cantidad_num = float(detalle.cantidad) if detalle.cantidad else 0.0
    precio_unit_num = parsear_monto(detalle.precio_unit)

    # Calcular total del item
    total_item = cantidad_num * precio_unit_num

    # La moneda puede ser USD o CRC
    moneda = orden.moneda if orden.moneda else "USD"

    with engine.connect() as conn:
        conn.execute(
            text(query_insert_orden_item_stg),
            {
                "source_system": "mysql",
                "source_key_orden": str(orden.id),
                "source_key_item": str(detalle.id),
                "source_code_prod": codigo_alt,
                "cliente_key": str(orden.cliente_id),
                "fecha_raw": str(fecha_raw),
                "canal_raw": canal_raw,
                "moneda": moneda,
                "cantidad_raw": str(detalle.cantidad),
                "precio_unit_raw": str(detalle.precio_unit),
                "total_raw": str(total_item),
                "fecha_dt": fecha_dt,
                "cantidad_num": cantidad_num,
                "precio_unit_num": precio_unit_num,
                "total_num": total_item,
            },
        )
        conn.commit()


# -----------------------------------------------------------------------
#         Función principal de transformación de datos de MySQL
# -----------------------------------------------------------------------


def transform_mysql(clientes, productos, ordenes, orden_detalles):
    """
    Transforma y carga los datos de MySQL en las tablas de staging.

    Args:
        clientes: Lista de clientes extraídos
        productos: Lista de productos extraídos
        ordenes: Lista de órdenes extraídas
        orden_detalles: Lista de detalles de órdenes extraídos
    """
    total_items = len(orden_detalles)

    # Dictionary to track assigned SKUs
    sku_mapping = {}

    # 1. Process clients
    for i, cliente in enumerate(clientes):
        insert_clientes_stg(cliente)
        if (i + 1) % 50 == 0 or i == len(clientes) - 1:
            print(
                f"\r    mysql: {i + 1}/{len(clientes)} clients...",
                end="",
                flush=True,
            )

    # 2. Process products and create mapping table
    productos_dict = {}  # {producto_id: codigo_alt}
    for i, producto in enumerate(productos):
        insert_map_producto(producto, sku_mapping)
        productos_dict[producto.id] = producto.codigo_alt
        if (i + 1) % 50 == 0 or i == len(productos) - 1:
            print(
                f"\r    mysql: {len(clientes)} clients | {i + 1}/{len(productos)} products...",
                end="",
                flush=True,
            )

    # 3. Process orders and details
    ordenes_dict = {orden.id: orden for orden in ordenes}

    items_procesados = 0
    errores = 0
    for detalle in orden_detalles:
        orden = ordenes_dict.get(detalle.orden_id)
        if orden:
            try:
                insert_orden_items_stg(orden, detalle, productos_dict)
                items_procesados += 1
            except Exception:
                errores += 1

            if (items_procesados + errores) % 100 == 0 or (
                items_procesados + errores
            ) == total_items:
                print(
                    f"\r    mysql: {len(clientes)} clients | {len(productos)} products | {items_procesados}/{total_items} items...",
                    end="",
                    flush=True,
                )

    # Final line
    output = f"\r    mysql: {len(clientes)} clients | {len(productos)} products | {items_procesados} items"
    if errores > 0:
        output += f" | {errores} errors"
    print(output + " " * 20)  # Extra spaces to clear progress indicators
