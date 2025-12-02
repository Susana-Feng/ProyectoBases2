from config.database import supabase
from datetime import datetime
from postgrest import APIError as PostgrestAPIError
from typing import Any, Optional
import json


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _coerce_json_payload(payload: Any) -> Optional[dict]:
    """Best-effort conversion of Supabase payloads (bytes/strings) into dicts."""
    if payload is None:
        return None
    if isinstance(payload, dict):
        return payload

    text: Optional[str] = None
    if isinstance(payload, (bytes, bytearray)):
        text = payload.decode("utf-8", errors="ignore")
    elif isinstance(payload, str):
        text = payload
    elif isinstance(payload, (list, tuple)):
        # Stored procedures normally return a single row, but if we somehow get
        # a list, inspect the first element.
        return _coerce_json_payload(payload[0]) if payload else None

    if text is None:
        return None

    cleaned = text.strip()
    if cleaned.startswith('b"') and cleaned.endswith('"'):
        cleaned = cleaned[2:-1]
    if cleaned.startswith("b'") and cleaned.endswith("'"):
        cleaned = cleaned[2:-1]

    if not cleaned:
        return None

    for candidate in (cleaned, cleaned.replace("'", '"')):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = cleaned[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return None
    return None


def _normalize_rpc_data(data: Any) -> Any:
    parsed = _coerce_json_payload(data)
    return parsed if parsed is not None else data


def _extract_success_from_error(error: Exception) -> Optional[dict]:
    candidates = []

    if hasattr(error, "details"):
        candidates.append(getattr(error, "details"))

    if error.args:
        candidates.extend(error.args)

    for candidate in candidates:
        parsed = _coerce_json_payload(candidate)
        if parsed and str(parsed.get("status", "")).lower() == "success":
            return parsed
        if isinstance(candidate, dict):
            details = candidate.get("details")
            parsed_details = _coerce_json_payload(details)
            if (
                parsed_details
                and str(parsed_details.get("status", "")).lower() == "success"
            ):
                return parsed_details
    return None


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

        data = _normalize_rpc_data(response.data)

        print("✅ Orden creada:", data)
        return data
    except PostgrestAPIError as e:
        parsed = _extract_success_from_error(e)
        if parsed:
            print("✅ Orden creada:", parsed)
            return parsed
        print("❌ Error al crear orden:", e)
        return {"error": str(e)}
    except Exception as e:
        print("❌ Error al crear orden:", e)
        return {"error": str(e)}


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


def _map_items_by_order(order_ids):
    if not order_ids:
        return {}, {}

    try:
        details_response = (
            supabase.table("orden_completa")
            .select(
                "orden_id, producto_id, cantidad, precio_unitario, nombre_producto, cliente_id, nombre_cliente"
            )
            .in_("orden_id", order_ids)
            .execute()
        )

        items_map = {oid: [] for oid in order_ids}
        clientes_map = {}

        for detail in details_response.data or []:
            oid = detail.get("orden_id")
            if not oid:
                continue

            items_map.setdefault(oid, []).append(
                {
                    "producto_id": detail.get("producto_id"),
                    "cantidad": detail.get("cantidad"),
                    "precio_unitario": detail.get("precio_unitario"),
                    "producto": {
                        "producto_id": detail.get("producto_id"),
                        "nombre": detail.get("nombre_producto"),
                    },
                }
            )

            if oid not in clientes_map:
                clientes_map[oid] = {
                    "cliente_id": detail.get("cliente_id"),
                    "nombre": detail.get("nombre_cliente"),
                }

        return items_map, clientes_map
    except Exception as e:
        print("❌ Error agrupando items de órdenes:", e)
        return {oid: [] for oid in order_ids}, {}


def _count_orders_total():
    try:
        response = (
            supabase.table("orden").select("orden_id", count="exact").limit(1).execute()
        )
        return response.count or 0
    except Exception as e:
        print("❌ Error obteniendo total de órdenes:", e)
        return 0


def get_orders(offset: int = 0, limit: int = 10):
    try:
        total_orders = _count_orders_total()

        orders_response = (
            supabase.table("orden")
            .select("orden_id, fecha, canal, moneda, total, cliente_id")
            .order("fecha", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        order_rows = orders_response.data or []
        order_ids = [row.get("orden_id") for row in order_rows if row.get("orden_id")]

        items_map, clientes_map = _map_items_by_order(order_ids)

        orders = []
        for row in order_rows:
            oid = row.get("orden_id")
            if not oid:
                continue

            cliente_info = clientes_map.get(
                oid,
                {
                    "cliente_id": row.get("cliente_id"),
                    "nombre": None,
                },
            )

            orders.append(
                {
                    "orden_id": oid,
                    "fecha": row.get("fecha"),
                    "canal": row.get("canal"),
                    "moneda": row.get("moneda"),
                    "total": row.get("total"),
                    "cliente": cliente_info,
                    "items": items_map.get(oid, []),
                }
            )

        print(
            f"✅ Órdenes obtenidas: {len(orders)} (offset={offset}, limit={limit}, total={total_orders})"
        )

        return {
            "offset": offset,
            "limit": limit,
            "total": total_orders,
            "count": len(orders),
            "data": orders,
        }
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
