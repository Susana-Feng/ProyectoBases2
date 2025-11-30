from configs.connections import get_supabase_client


# -------------------------------------------
# Pagination helper for Supabase (default limit is 1000)
# -------------------------------------------
def fetch_all_paginated(supabase, table_name: str, page_size: int = 1000) -> list:
    """
    Fetch all records from a Supabase table using pagination.
    Supabase has a default limit of 1000 rows per query.
    """
    all_data = []
    offset = 0

    while True:
        response = (
            supabase.table(table_name)
            .select("*")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        if hasattr(response, "error") and response.error:
            raise Exception(f"Error fetching {table_name}: {response.error}")

        batch = response.data
        if not batch:
            break

        all_data.extend(batch)

        # If we got fewer records than page_size, we've reached the end
        if len(batch) < page_size:
            break

        offset += page_size

    return all_data


# -------------------------------------------
# 1. Crear función extract_supabase
# -------------------------------------------
def extract_supabase():
    """
    Extrae los registros de múltiples tablas en Supabase.

    Returns:
        tuple: (clientes, productos, ordenes, orden_detalles)
    """
    supabase = get_supabase_client()

    # Fetch all records using pagination
    clientes = fetch_all_paginated(supabase, "cliente")
    productos = fetch_all_paginated(supabase, "producto")
    ordenes = fetch_all_paginated(supabase, "orden")
    orden_detalles = fetch_all_paginated(supabase, "orden_detalle")

    print(
        f"    supab: {len(clientes)} clients | {len(productos)} products | {len(ordenes)} orders | {len(orden_detalles)} items"
    )

    return clientes, productos, ordenes, orden_detalles
