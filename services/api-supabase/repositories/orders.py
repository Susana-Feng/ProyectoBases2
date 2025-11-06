from config.database import supabase
from datetime import datetime, date

# --------------------------------------------------
# CRUD Functions using Supabase RPC
# --------------------------------------------------
def create_order(p_canal, p_cliente_id, p_fecha, p_items, p_moneda):
    try:
        response = supabase.rpc(
            'fn_crear_orden',
            {
                'p_canal': p_canal,
                'p_cliente_id': p_cliente_id,
                'p_fecha': p_fecha,
                'p_items': p_items,
                'p_moneda': p_moneda
            }
        ).execute()

        print("✅ Orden creada:", response.data)
        return response.data

    except Exception as e:
        print("❌ Error al crear orden:", e)
        return None


def update_order(p_canal, p_cliente_id, p_fecha, p_items, p_moneda, p_orden_id):
    try:
        response = supabase.rpc(
            'fn_actualizar_orden_completa',
            {
                'p_canal': p_canal,
                'p_cliente_id': p_cliente_id,
                'p_fecha': p_fecha,
                'p_items': p_items,
                'p_moneda': p_moneda,
                'p_orden_id': p_orden_id
            }
        ).execute()

        print("✅ Orden actualizada completamente:", response.data)
        return response.data

    except Exception as e:
        print("❌ Error al actualizar orden completa:", e)
        return None

def delete_order(p_orden_id):
    try:
        response = supabase.rpc(
            'fn_eliminar_orden',
            {'p_orden_id': p_orden_id}
        ).execute()

        print("✅ Orden eliminada:", response.data)
        return response.data

    except Exception as e:
        print("❌ Error al eliminar orden:", e)
        return None

def get_orders():
    try:
        response = (
            supabase.table("orden_completa")
            .select("*")
            .range(0, 9)
            .execute()
        )

        if response.data:
            print("✅ Órdenes completas:", response.data)
            return response.data
        else:
            print("⚠️ No se encontraron registros o hubo error:", response)
            return None

    except Exception as e:
        print("❌ Error al obtener órdenes completas:", e)
        return None
        
class OrderRepository:
    @staticmethod
    def get_orders():
        return get_orders()

    @staticmethod
    def create_order(p_canal, p_cliente_id, p_fecha, p_items, p_moneda):
        return create_order(p_canal, p_cliente_id, p_fecha, p_items, p_moneda)

    @staticmethod
    def update_order(p_canal, p_cliente_id, p_fecha, p_items, p_moneda, p_orden_id):
        return update_order(p_canal, p_cliente_id, p_fecha, p_items, p_moneda, p_orden_id)

    @staticmethod
    def delete_order(p_orden_id):
        return delete_order(p_orden_id)