from config.database import supabase
from datetime import datetime
import json


# --------------------------------------------------
# CRUD Functions using Supabase RPC
# --------------------------------------------------
def create_order(canal, cliente_id, fecha, items, moneda):
    try:
        if isinstance(fecha, datetime):
            fecha = fecha.isoformat()

        response = supabase.rpc(
            "fn_crear_orden",
            {
                "p_canal": canal,
                "p_cliente_id": cliente_id,
                "p_fecha": fecha,
                "p_items": items,
                "p_moneda": moneda,
            },
        ).execute()

        data = response.data

        # Manejar diferentes formatos de respuesta
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # Si no es JSON válido, retornar como dict simple
                data = {"status": "success", "raw_response": data}

        print("✅ Orden creada:", data)
        return data

    except Exception as e:
        print("❌ Error al crear orden:", e)
        return None


def update_order(canal, cliente_id, fecha, items, moneda, orden_id):
    try:
        if isinstance(fecha, datetime):
            fecha = fecha.isoformat()

        response = supabase.rpc(
            "fn_actualizar_orden_completa",
            {
                "p_canal": canal,
                "p_cliente_id": cliente_id,
                "p_fecha": fecha,
                "p_items": items,
                "p_moneda": moneda,
                "p_orden_id": orden_id,
            },
        ).execute()

        print("✅ Orden actualizada completamente:", response.data)
        return response.data

    except Exception as e:
        print("❌ Error al actualizar orden completa:", e)
        return None


def delete_order(p_orden_id):
    try:
        response = supabase.rpc(
            "fn_eliminar_orden", {"p_orden_id": p_orden_id}
        ).execute()

        print("✅ Orden eliminada:", response.data)
        return response.data

    except Exception as e:
        print("❌ Error al eliminar orden:", e)
        return None


def get_orders(offset: int = 0, limit: int = 10):
    try:
        response = (
            supabase.table("orden_completa")
            .select("*")
            .range(offset, offset + limit - 1)
            .order("fecha", desc=True)
            .execute()
        )

        if response.data:
            print(
                f"✅ Órdenes obtenidas: {len(response.data)} (offset={offset}, limit={limit})"
            )
            return response.data
        else:
            print("⚠️ No se encontraron registros o hubo error:", response)
            return []
    except Exception as e:
        print("❌ Error en OrderRepository.get_orders:", e)
        return {"error": str(e)}


class OrderRepository:
    @staticmethod
    def get_orders(offset: int = 0, limit: int = 10):
        return get_orders(offset, limit)

    @staticmethod
    def create_order(canal, cliente_id, fecha, items, moneda):
        return create_order(canal, cliente_id, fecha, items, moneda)

    @staticmethod
    def update_order(canal, cliente_id, fecha, items, moneda, orden_id):
        return update_order(canal, cliente_id, fecha, items, moneda, orden_id)

    @staticmethod
    def delete_order(p_orden_id):
        return delete_order(p_orden_id)
