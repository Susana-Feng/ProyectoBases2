from configs.connections import get_supabase_client

# -------------------------------------------
# 1. Crear función extract_supabase
# -------------------------------------------
def extract_supabase():
    """
    Extrae los registros de múltiples tablas en Supabase
    y devuelve un diccionario con listas de diccionarios.
    """
    supabase = get_supabase_client()

    # Consultas a cada tabla
    response_cliente = supabase.table("cliente").select("*").execute()
    response_orden_completa = supabase.table("orden_completa").select("*").execute()
    response_producto = supabase.table("producto").select("*").execute()

    # Validación de errores
    for resp in [
        response_cliente,
        response_orden_completa,
        response_producto,
    ]:
        if hasattr(resp, "error") and resp.error:
            raise Exception(f"Error al extraer datos: {resp.error}")


    # Mostrar estadísticas de extracción
    print(f"[Supabase Extract] Productos extraídos: {len(response_producto.data)}")
    print(f"[Supabase Extract] Clientes extraídos: {len(response_cliente.data)}")
    print(f"[Supabase Extract] Órdenes extraídas: {len(response_orden_completa.data)}")

    # Devolver todas las tablas como diccionario
    return response_cliente.data, response_orden_completa.data, response_producto.data