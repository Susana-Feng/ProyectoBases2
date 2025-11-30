from configs.connections import get_dw_engine
from sqlalchemy import text
from datetime import datetime, timedelta

engine = get_dw_engine()

""" -----------------------------------------------------------------------
            Queries de SQL para cargar el DataWarehouse
    ----------------------------------------------------------------------- """

query_check_last_load = """
    SELECT 
        COALESCE(MAX(LoadTS), '1900-01-01') AS LastLoadTS
    FROM {table_name}
"""

query_insert_DimTime = """
    -- Start 3 years ago (matches BCCR exchange rate history)
    DECLARE @FechaInicio DATE = DATEADD(YEAR, -3, CAST(GETDATE() AS DATE));
    DECLARE @FechaFin    DATE = CAST(GETDATE() AS DATE);

    ;WITH Fechas AS (
        SELECT @FechaInicio AS Fecha
        UNION ALL
        SELECT DATEADD(DAY, 1, Fecha)
        FROM Fechas
        WHERE Fecha < @FechaFin
    )
    INSERT INTO dw.DimTiempo (
        TiempoID, Fecha, Anio, Mes, Dia, LoadTS
    )
    SELECT
        CONVERT(INT, FORMAT(Fecha, 'yyyyMMdd')) AS TiempoID,
        Fecha,
        YEAR(Fecha) AS Anio,
        MONTH(Fecha) AS Mes,
        DAY(Fecha) AS Dia,
        GETDATE() AS LoadTS
    FROM Fechas
    WHERE NOT EXISTS (
        SELECT 1 FROM dw.DimTiempo dt WHERE dt.Fecha = Fechas.Fecha
    )
    OPTION (MAXRECURSION 0);
"""

query_sync_exchange_rates = """
    -- Sync exchange rates from stg.tipo_cambio to dw.DimTiempo
    UPDATE dt
    SET 
        dt.TC_CRC_USD = tc_crc.tasa,
        dt.TC_USD_CRC = tc_usd.tasa
    FROM dw.DimTiempo dt
    LEFT JOIN stg.tipo_cambio tc_crc 
        ON tc_crc.fecha = dt.Fecha AND tc_crc.de = 'CRC' AND tc_crc.a = 'USD'
    LEFT JOIN stg.tipo_cambio tc_usd 
        ON tc_usd.fecha = dt.Fecha AND tc_usd.de = 'USD' AND tc_usd.a = 'CRC'
    WHERE dt.TC_CRC_USD IS NULL 
       OR dt.TC_USD_CRC IS NULL
       OR dt.TC_CRC_USD != COALESCE(tc_crc.tasa, dt.TC_CRC_USD)
       OR dt.TC_USD_CRC != COALESCE(tc_usd.tasa, dt.TC_USD_CRC);
"""

query_insert_dimCliente_dw = """
    INSERT INTO dw.DimCliente (
        SourceSystem,
        SourceKey,
        Email,
        Nombre,
        Genero,
        Pais,
        FechaCreacionID,
        LoadTS
    )
    SELECT
        :sourceSystem,
        :sourceKey,
        :Email,
        :Nombre,
        :Genero,
        :Pais,
        TiempoID,
        GETDATE() AS LoadTS
    FROM dw.DimTiempo
    WHERE Fecha = :FechaCreacion
        AND NOT EXISTS (
            SELECT 1 FROM dw.DimCliente dc 
            WHERE dc.SourceSystem = :sourceSystem 
            AND dc.SourceKey = :sourceKey
        );
"""

query_check_existing_cliente = """
    SELECT COUNT(*) 
    FROM dw.DimCliente 
    WHERE SourceSystem = :SourceSystem AND SourceKey = :SourceKey
"""

query_select_clientes_stg = """
    SELECT
        C.source_system AS sourceSystem,
        C.source_code AS sourceCode,
        C.cliente_email AS Email,
        C.cliente_nombre AS Nombre,
        C.genero_norm AS Genero,
        C.pais_raw AS Pais,
        C.fecha_creado_dt AS FechaCreacion,
        C.load_ts AS SourceLoadTS
    FROM stg.clientes AS C
    WHERE C.load_ts > :last_load_ts
"""

query_select_map_producto = """
    SELECT
        P.source_system AS SourceSystem,
        P.source_code AS SourceKey,
        P.nombre_norm AS Nombre,
        P.categoria_norm AS Categoria,
        P.es_servicio AS EsServicio,
        P.sku_oficial AS SKU
    FROM stg.map_producto AS P
"""

query_select_map_producto_new = """
    SELECT
        P.source_system AS SourceSystem,
        P.source_code AS SourceKey,
        P.nombre_norm AS Nombre,
        P.categoria_norm AS Categoria,
        P.es_servicio AS EsServicio,
        P.sku_oficial AS SKU
    FROM stg.map_producto AS P
    WHERE NOT EXISTS (
        SELECT 1 FROM dw.DimProducto dp 
        WHERE dp.SourceSystem = P.source_system 
        AND dp.SourceKey = P.source_code
    )
"""

query_insert_dimProducto_dw = """
    INSERT INTO dw.DimProducto (
        SKU,
        Nombre,
        Categoria,
        EsServicio,
        SourceSystem,
        SourceKey,
        LoadTS
    )
    VALUES (
        :SKU,
        :Nombre,
        :Categoria,
        :EsServicio,
        :SourceSystem,
        :SourceKey,
        GETDATE()
    )
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
        SourceKey,
        LoadTS
    )
    SELECT
        T.TiempoID,
        C.ClienteID,
        P.ProductoID,
        O.canal_raw,
        O.source_system,
        O.cantidad_num,
        -- Convert to USD using official exchange rate only
        CASE 
            WHEN O.moneda = 'USD' THEN O.precio_unit_num
            WHEN O.moneda = 'CRC' THEN O.precio_unit_num / T.TC_CRC_USD
            ELSE O.precio_unit_num
        END AS PrecioUnitUSD,
        CASE 
            WHEN O.moneda = 'USD' THEN O.total_num
            WHEN O.moneda = 'CRC' THEN O.total_num / T.TC_CRC_USD
            ELSE O.total_num
        END AS TotalUSD,
        O.moneda,
        O.precio_unit_num,
        O.total_num,
        O.source_key_orden + '-' + O.source_key_item,
        GETDATE() AS LoadTS
    FROM stg.orden_items AS O
    INNER JOIN dw.DimTiempo AS T
        ON T.Fecha = O.fecha_dt
    INNER JOIN dw.DimCliente AS C
        ON O.cliente_key = C.SourceKey
        AND O.source_system = C.SourceSystem
    INNER JOIN dw.DimProducto AS P
        ON O.source_code_prod = P.SourceKey
        AND O.source_system = P.SourceSystem
    WHERE O.load_ts > :last_load_ts
        AND NOT EXISTS (
            SELECT 1 FROM dw.FactVentas fv
            WHERE fv.SourceKey = O.source_key_orden + '-' + O.source_key_item
            AND fv.Fuente = O.source_system
        )
        -- Exclude CRC sales without exchange rate (must have official rate)
        AND (O.moneda != 'CRC' OR T.TC_CRC_USD IS NOT NULL)
"""

query_select_new_orders = """
    SELECT COUNT(*) AS NewRecords
    FROM stg.orden_items
    WHERE load_ts > :last_load_ts
"""

query_check_existing_product = """
    SELECT COUNT(*) 
    FROM dw.DimProducto 
    WHERE SourceSystem = :SourceSystem AND SourceKey = :SourceKey
"""

query_check_existing_sku = """
    SELECT COUNT(*) 
    FROM dw.DimProducto 
    WHERE SKU = :SKU
"""

""" -----------------------------------------------------------------------
            Funciones auxiliares para cargar el DataWarehouse
    ----------------------------------------------------------------------- """


def get_last_load_timestamp(conn, table_name):
    """Obtiene el último timestamp de carga de una tabla del DW"""
    query = text(query_check_last_load.format(table_name=table_name))
    result = conn.execute(query)
    last_load = result.fetchone()[0]
    return last_load


def should_run_process(conn):
    """Verifica si el proceso debe ejecutarse basado en los últimos LoadTS"""

    # Obtener el último LoadTS de cada dimensión
    last_load_tiempo = get_last_load_timestamp(conn, "dw.DimTiempo")
    last_load_cliente = get_last_load_timestamp(conn, "dw.DimCliente")
    last_load_producto = get_last_load_timestamp(conn, "dw.DimProducto")
    last_load_ventas = get_last_load_timestamp(conn, "dw.FactVentas")

    # Verificar si hay datos nuevos en las tablas de staging
    current_time = datetime.now()

    # Si alguna dimensión no tiene datos recientes (menos de 24 horas), ejecutar
    time_threshold = current_time - timedelta(hours=24)

    if (
        last_load_tiempo < time_threshold
        or last_load_cliente < time_threshold
        or last_load_producto < time_threshold
        or last_load_ventas < time_threshold
    ):
        return True, "Proceso programado (más de 24 horas desde última ejecución)"

    # Verificar si hay nuevos datos en las tablas de staging
    try:
        # Verificar nuevas órdenes
        result = conn.execute(
            text(query_select_new_orders), {"last_load_ts": last_load_ventas}
        )
        new_orders = result.fetchone()[0]

        if new_orders > 0:
            return True, f"Se encontraron {new_orders} nuevas órdenes para procesar"

        # Verificar nuevos clientes
        result = conn.execute(
            text(query_select_clientes_stg), {"last_load_ts": last_load_cliente}
        )
        new_clientes = len(result.fetchall())

        if new_clientes > 0:
            return True, f"Se encontraron {new_clientes} nuevos clientes para procesar"

    except Exception as e:
        print(f"Error en verificación: {e}")
        # Si hay error en la verificación, ejecutar el proceso por seguridad
        return True, "Error en verificación, ejecutando proceso por seguridad"

    return False, "No hay datos nuevos para procesar"


def get_clientes_stg(conn, last_load_ts):
    """Obtiene clientes nuevos desde el staging"""
    result = conn.execute(
        text(query_select_clientes_stg), {"last_load_ts": last_load_ts}
    )
    clientes_stg = result.fetchall()
    return clientes_stg


def get_map_productos(conn):
    """Obtiene todos los productos desde el staging (sin load_ts)"""
    result = conn.execute(text(query_select_map_producto))
    productos_stg = result.fetchall()
    return productos_stg


def get_new_map_productos(conn):
    """Obtiene solo productos nuevos que no existen en el DW"""
    result = conn.execute(text(query_select_map_producto_new))
    productos_stg = result.fetchall()
    return productos_stg


def product_exists(conn, source_system, source_key):
    """Verifica si un producto ya existe en el DW por SourceSystem/SourceKey"""
    result = conn.execute(
        text(query_check_existing_product),
        {"SourceSystem": source_system, "SourceKey": source_key},
    )
    return result.fetchone()[0] > 0


def sku_exists(conn, sku):
    """Verifica si un SKU ya existe en el DW"""
    if not sku:
        return False
    result = conn.execute(
        text(query_check_existing_sku),
        {"SKU": sku},
    )
    return result.fetchone()[0] > 0


def cliente_exists(conn, source_system, source_key):
    """Verifica si un cliente ya existe en el DW"""
    result = conn.execute(
        text(query_check_existing_cliente),
        {"SourceSystem": source_system, "SourceKey": source_key},
    )
    return result.fetchone()[0] > 0


def load_dim_tiempo(conn):
    """Load DimTiempo and sync exchange rates from stg.tipo_cambio"""
    # Check if we have dates up to today
    query_check_dates = """
        SELECT MAX(Fecha) AS MaxFecha 
        FROM dw.DimTiempo
        WHERE Fecha <= CAST(GETDATE() AS DATE)
    """
    result = conn.execute(text(query_check_dates))
    max_fecha = result.fetchone()[0]

    current_date = datetime.now().date()
    dates_status = "up to date"

    if not max_fecha or max_fecha < current_date:
        conn.exec_driver_sql(query_insert_DimTime)
        dates_status = "dates updated"

    # Always sync exchange rates from stg.tipo_cambio
    result = conn.execute(text(query_sync_exchange_rates))
    tc_synced = result.rowcount

    if tc_synced > 0:
        return f"{dates_status}, {tc_synced} exchange rates synced"
    return dates_status


def load_dim_cliente(conn):
    """Carga solo clientes nuevos, evitando duplicados"""
    last_load_ts = get_last_load_timestamp(conn, "dw.DimCliente")
    clientes_stg = get_clientes_stg(conn, last_load_ts)

    if not clientes_stg:
        return 0, 0, {}

    loaded_count = 0
    skipped_count = 0
    by_source = {}

    for cliente in clientes_stg:
        source = cliente.sourceSystem
        if source not in by_source:
            by_source[source] = 0
        
        # Double check to avoid duplicates
        if not cliente_exists(conn, cliente.sourceSystem, cliente.sourceCode):
            conn.execute(
                text(query_insert_dimCliente_dw),
                {
                    "sourceSystem": cliente.sourceSystem,
                    "sourceKey": cliente.sourceCode,
                    "Email": cliente.Email,
                    "Nombre": cliente.Nombre,
                    "Genero": cliente.Genero,
                    "Pais": cliente.Pais,
                    "FechaCreacion": cliente.FechaCreacion,
                },
            )
            loaded_count += 1
            by_source[source] += 1
        else:
            skipped_count += 1

    return loaded_count, skipped_count, by_source


def load_dim_producto(conn):
    """Carga productos - maneja la falta de load_ts en map_producto"""

    # Load only new products (recommended for production)
    productos_stg = get_new_map_productos(conn)

    if not productos_stg:
        return 0, {}

    loaded_count = 0
    skipped_count = 0
    by_source = {}
    
    for producto in productos_stg:
        source = producto.SourceSystem
        if source not in by_source:
            by_source[source] = 0
            
        # Check by (SourceSystem, SourceKey) AND by SKU to avoid duplicates
        if product_exists(conn, producto.SourceSystem, producto.SourceKey):
            skipped_count += 1
            continue
        if sku_exists(conn, producto.SKU):
            # SKU already exists from another source, skip
            skipped_count += 1
            continue

        conn.execute(
            text(query_insert_dimProducto_dw),
            {
                "SourceSystem": producto.SourceSystem,
                "SourceKey": producto.SourceKey,
                "SKU": producto.SKU,
                "Nombre": producto.Nombre,
                "Categoria": producto.Categoria,
                "EsServicio": producto.EsServicio,
            },
        )
        loaded_count += 1
        by_source[source] += 1

    return loaded_count, by_source


def load_dim_producto_initial(conn):
    """Carga inicial de todos los productos (usar solo primera vez)"""
    productos_stg = get_map_productos(conn)

    if not productos_stg:
        return 0

    loaded_count = 0
    for producto in productos_stg:
        # Check by (SourceSystem, SourceKey) AND by SKU to avoid duplicates
        if product_exists(conn, producto.SourceSystem, producto.SourceKey):
            continue
        if sku_exists(conn, producto.SKU):
            continue

        conn.execute(
            text(query_insert_dimProducto_dw),
            {
                "SourceSystem": producto.SourceSystem,
                "SourceKey": producto.SourceKey,
                "SKU": producto.SKU,
                "Nombre": producto.Nombre,
                "Categoria": producto.Categoria,
                "EsServicio": producto.EsServicio,
            },
        )
        loaded_count += 1

    return loaded_count


def load_fact_ventas(conn):
    """Carga solo ventas nuevas, evitando duplicados"""
    last_load_ts = get_last_load_timestamp(conn, "dw.FactVentas")

    count_by_source_query = "SELECT Fuente, COUNT(*) AS cnt FROM dw.FactVentas GROUP BY Fuente"

    # Check if there are new sales in staging
    result = conn.execute(text(query_select_new_orders), {"last_load_ts": last_load_ts})
    new_records = result.fetchone()[0]

    if new_records == 0:
        return 0, 0, None, {}

    # Count records before by source
    before_by_source = {}
    for row in conn.execute(text(count_by_source_query)):
        before_by_source[row.Fuente] = row.cnt
    count_before = sum(before_by_source.values())

    # Insert (query already has NOT EXISTS to avoid duplicates)
    conn.execute(text(query_insert_factVentas), {"last_load_ts": last_load_ts})

    # Count records after by source
    after_by_source = {}
    for row in conn.execute(text(count_by_source_query)):
        after_by_source[row.Fuente] = row.cnt
    count_after = sum(after_by_source.values())

    loaded_count = count_after - count_before
    skipped_count = new_records - loaded_count
    
    # Calculate loaded by source
    by_source = {}
    for source in after_by_source:
        before = before_by_source.get(source, 0)
        after = after_by_source[source]
        if after - before > 0:
            by_source[source] = after - before

    # Diagnostic: check why records were skipped
    diagnostics = None
    diagnostic_query = """
        SELECT 
            'No DimTiempo' AS Reason,
            COUNT(*) AS Count
        FROM stg.orden_items O
        WHERE O.load_ts > :last_load_ts
            AND NOT EXISTS (SELECT 1 FROM dw.DimTiempo T WHERE T.Fecha = O.fecha_dt)
        UNION ALL
        SELECT 
            'No DimCliente' AS Reason,
            COUNT(*) AS Count
        FROM stg.orden_items O
        WHERE O.load_ts > :last_load_ts
            AND NOT EXISTS (
                SELECT 1 FROM dw.DimCliente C 
                WHERE C.SourceKey = O.cliente_key AND C.SourceSystem = O.source_system
            )
        UNION ALL
        SELECT 
            'No DimProducto' AS Reason,
            COUNT(*) AS Count
        FROM stg.orden_items O
        WHERE O.load_ts > :last_load_ts
            AND NOT EXISTS (
                SELECT 1 FROM dw.DimProducto P 
                WHERE P.SourceKey = O.source_code_prod AND P.SourceSystem = O.source_system
            )
        UNION ALL
        SELECT 
            'Duplicate' AS Reason,
            COUNT(*) AS Count
        FROM stg.orden_items O
        WHERE O.load_ts > :last_load_ts
            AND EXISTS (
                SELECT 1 FROM dw.FactVentas fv
                WHERE fv.SourceKey = O.source_key_orden + '-' + O.source_key_item
                AND fv.Fuente = O.source_system
            )
        UNION ALL
        SELECT 
            'CRC without exchange rate (run BCCR job)' AS Reason,
            COUNT(*) AS Count
        FROM stg.orden_items O
        INNER JOIN dw.DimTiempo T ON T.Fecha = O.fecha_dt
        WHERE O.load_ts > :last_load_ts
            AND O.moneda = 'CRC'
            AND T.TC_CRC_USD IS NULL
    """
    diag_result = conn.execute(text(diagnostic_query), {"last_load_ts": last_load_ts})
    diagnostics = [(row.Reason, row.Count) for row in diag_result if row.Count > 0]

    return loaded_count, skipped_count, diagnostics if diagnostics else None, by_source


def check_exchange_rate_coverage(conn):
    """Check for dates with CRC sales but no exchange rate after sync"""
    query = """
        SELECT 
            COUNT(DISTINCT O.fecha_dt) AS missing_dates,
            COUNT(*) AS missing_records
        FROM stg.orden_items O
        INNER JOIN dw.DimTiempo T ON T.Fecha = O.fecha_dt
        WHERE O.moneda = 'CRC' AND T.TC_CRC_USD IS NULL
    """
    result = conn.execute(text(query))
    row = result.fetchone()
    return row[0], row[1]  # dates, records


""" -----------------------------------------------------------------------
            Main function to load the DataWarehouse
    ----------------------------------------------------------------------- """


def format_by_source(by_source):
    """Format source counts in consistent order"""
    order = ["mssql", "mysql", "supab", "mongo", "neo4j"]
    # Map supabase to supab for display
    display_map = {"supabase": "supab"}
    parts = []
    for src in order:
        # Check both original and mapped names
        count = by_source.get(src, 0)
        if count == 0:
            # Try the full name for supabase
            for full, short in display_map.items():
                if short == src:
                    count = by_source.get(full, 0)
                    break
        if count > 0:
            parts.append(f"{src}: {count}")
    return " | ".join(parts) if parts else ""


def load_datawarehouse():
    try:
        with engine.begin() as conn:
            # Check if process should run
            should_run, reason = should_run_process(conn)

            if not should_run:
                print(f"    Skipped: {reason}")
                return {"executed": False, "reason": reason}

            # Execute loads - DimTiempo now also syncs exchange rates from stg.tipo_cambio
            tiempo_status = load_dim_tiempo(conn)

            # Check exchange rate coverage AFTER sync
            missing_dates, missing_records = check_exchange_rate_coverage(conn)
            if missing_dates > 0:
                print(
                    f"    WARNING: {missing_records} CRC sales on {missing_dates} dates have no exchange rate"
                )
                print(
                    "             These will be EXCLUDED until BCCR job provides rates"
                )

            clientes_loaded, clientes_skipped, clientes_by_source = load_dim_cliente(conn)
            productos_loaded, productos_by_source = load_dim_producto(conn)
            ventas_loaded, ventas_skipped, diagnostics, ventas_by_source = load_fact_ventas(conn)

            # Print summary
            print(f"    DimTiempo: {tiempo_status}")

            cliente_msg = f"    DimCliente: {clientes_loaded} loaded"
            if clientes_skipped > 0:
                cliente_msg += f", {clientes_skipped} skipped"
            print(cliente_msg)
            if clientes_by_source:
                print(f"        {format_by_source(clientes_by_source)}")

            print(f"    DimProducto: {productos_loaded} loaded")
            if productos_by_source:
                print(f"        {format_by_source(productos_by_source)}")

            ventas_msg = f"    FactVentas: {ventas_loaded} loaded"
            if ventas_skipped > 0:
                ventas_msg += f", {ventas_skipped} skipped"
            print(ventas_msg)
            if ventas_by_source:
                print(f"        {format_by_source(ventas_by_source)}")

            # Show diagnostics if there were skipped records
            if diagnostics:
                for reason, count in diagnostics:
                    print(f"      - {reason}: {count}")

            return "OK"

    except Exception as e:
        print(f"    Error: {str(e)}")
        raise
