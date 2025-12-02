import logging
from typing import List, Dict, Any
from fastapi import HTTPException
from schemas.orders import Order
from repositories.orders import OrderRepository
from neo4j.time import DateTime  # Importar el tipo de fecha de Neo4j

logger = logging.getLogger(__name__)


class OrdersController:
    @staticmethod
    def _normalize_id(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _normalize_items(items: List[Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for item in items:
            producto_id = (
                item.get("producto_id")
                if isinstance(item, dict)
                else getattr(item, "producto_id", "")
            )
            cantidad = (
                item.get("cantidad")
                if isinstance(item, dict)
                else getattr(item, "cantidad", None)
            )
            precio_unit = (
                item.get("precio_unit")
                if isinstance(item, dict)
                else getattr(item, "precio_unit", None)
            )

            normalized.append(
                {
                    "producto_id": OrdersController._normalize_id(producto_id),
                    "cantidad": cantidad,
                    "precio_unit": precio_unit,
                }
            )
        return normalized

    @staticmethod
    def _validate_references(cliente_id: str, items: List[Dict[str, Any]]):
        if not OrderRepository.client_exists(cliente_id):
            raise HTTPException(
                status_code=404,
                detail=f"Cliente {cliente_id} no existe en Neo4j",
            )

        missing_products = OrderRepository.missing_product_ids(
            [item.get("producto_id") for item in items]
        )
        if missing_products:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Productos no encontrados en Neo4j: " + ", ".join(missing_products)
                ),
            )

    @staticmethod
    def get_all_orders(skip: int = 0, limit: int = 10):
        try:
            # Validaciones básicas
            limit = min(limit, 100)  # evitar que pidan más de 100
            skip = max(skip, 0)

            # Leer datos paginados desde Neo4j
            orders_data = OrderRepository.read_orders(skip=skip, limit=limit)
            processed_orders = OrdersController._process_orders_data(orders_data)
            total = OrderRepository.count_orders()

            # Retornar resultado estructurado
            return {
                "skip": skip,
                "limit": limit,
                "total": total,
                "count": len(processed_orders),
                "data": processed_orders,
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving orders: {str(e)}"
            )

    @staticmethod
    def get_order_by_id(order_id: str):
        try:
            order_data = OrderRepository.read_order_by_id(order_id)
            if not order_data:
                raise HTTPException(
                    status_code=404, detail=f"order {order_id} not found"
                )

            processed_order = OrdersController._process_single_order_data(order_data)
            return processed_order
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving order: {str(e)}"
            )

    @staticmethod
    def _generate_order_id():
        """Genera un nuevo ID de orden automáticamente"""
        try:
            last_id = OrderRepository.get_last_order_id()
            print(f"Último ID encontrado: {last_id}")  # Debug

            if not last_id:
                return "O001"  # Primera orden

            # Extraer el número del último ID
            import re

            match = re.match(r"O(\d+)", last_id)
            if match:
                number = int(match.group(1))
                new_number = number + 1
                return f"O{new_number:03d}"  # Formato O001, O002, etc.
            else:
                # Si el formato no coincide, buscar el máximo numérico
                return "O001"

        except Exception as e:
            print(f"Error generando ID: {e}")
            return "O001"

    @staticmethod
    def _find_next_available_order_id(max_attempts=100):
        """Encuentra el próximo ID disponible verificando en la base de datos"""
        last_id = OrderRepository.get_last_order_id()

        if not last_id:
            return "ORD-000001"

        import re

        def _make_id(prefix: str, number: int, width: int) -> str:
            return f"{prefix}{number:0{width}d}"

        match = re.match(r"(ORD-)(\d+)", last_id) or re.match(r"(O)(\d+)", last_id)
        if match:
            prefix = match.group(1)
            digits = match.group(2)
            number = int(digits)
            width = len(digits)

            # Probar los siguientes N IDs
            for i in range(1, max_attempts + 1):
                potential_id = _make_id(prefix, number + i, width)
                existing = OrderRepository.read_order_by_id(potential_id)
                if not existing:
                    return potential_id

        # Si no encuentra después de max_attempts, reiniciar buscando huecos
        fallback_prefix = "ORD-"
        fallback_width = 6
        for i in range(1, max_attempts + 1):
            potential_id = _make_id(fallback_prefix, i, fallback_width)
            existing = OrderRepository.read_order_by_id(potential_id)
            if not existing:
                return potential_id

        # Último recurso: usar timestamp para no bloquear la inserción
        from datetime import datetime

        fallback = datetime.utcnow().strftime("ORD%Y%m%d%H%M%S")
        return fallback

    @staticmethod
    def create_order(order_data: Order):
        logger.info(
            "Creating Neo4j order",
            extra={"cliente_id": order_data.cliente_id, "items": len(order_data.items)},
        )
        try:
            auto_generated_id = OrdersController._find_next_available_order_id()
            print(f"ID generado: {auto_generated_id}")

            cliente_id = OrdersController._normalize_id(order_data.cliente_id)
            items_for_neo4j = OrdersController._normalize_items(order_data.items)

            OrdersController._validate_references(cliente_id, items_for_neo4j)

            success = OrderRepository.create_order(
                id=auto_generated_id,
                cliente_id=cliente_id,
                fecha=order_data.fecha,
                canal=order_data.canal.value,
                moneda=order_data.moneda.value,
                total=order_data.total,
                items=items_for_neo4j,
            )

            if success:
                return {
                    "orden_id": auto_generated_id,
                    "message": "Order created successfully",
                }
            else:
                raise HTTPException(
                    status_code=500, detail="Failed to create order in database"
                )

        except HTTPException as exc:
            logger.error("Neo4j create_order validation failed", exc_info=True)
            raise exc
        except Exception as e:
            logger.exception("Neo4j create_order unexpected error")
            raise HTTPException(
                status_code=500, detail=f"Error creating order: {str(e)}"
            )

    @staticmethod
    def update_order(order_id: str, order_data: Order):
        logger.info(
            "Updating Neo4j order",
            extra={"order_id": order_id, "cliente_id": order_data.cliente_id},
        )
        try:
            # Verificar que la orden existe
            existing_order = OrderRepository.read_order_by_id(order_id)
            if not existing_order:
                raise HTTPException(
                    status_code=404, detail=f"Orden {order_id} not found"
                )

            cliente_id = OrdersController._normalize_id(order_data.cliente_id)
            items_for_neo4j = OrdersController._normalize_items(order_data.items)

            OrdersController._validate_references(cliente_id, items_for_neo4j)

            # Actualizar la orden - usar la versión corregida
            success = OrderRepository.update_order_with_relationships(
                id=order_id,
                fecha=order_data.fecha,
                canal=order_data.canal.value,
                cliente_id=cliente_id,
                moneda=order_data.moneda.value,
                total=order_data.total,
                items=items_for_neo4j,
            )

            if success:
                return {"message": "Orden updated successfully"}
            else:
                raise HTTPException(
                    status_code=500, detail="Failed to update order in database"
                )

        except HTTPException as exc:
            logger.error(
                "Neo4j update_order validation failed",
                extra={"order_id": order_id},
                exc_info=True,
            )
            raise exc
        except Exception as e:
            logger.exception("Neo4j update_order unexpected error")
            raise HTTPException(
                status_code=500, detail=f"Error updating order: {str(e)}"
            )

    @staticmethod
    def delete_order(order_id: str):
        try:
            # Verificar que la order existe
            existing_order = OrderRepository.read_order_by_id(order_id)
            if not existing_order:
                raise HTTPException(
                    status_code=404, detail=f"order {order_id} not found"
                )

            OrderRepository.delete_order(order_id)
            return {"message": "order deleted"}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error deleting order: {str(e)}"
            )

    # Métodos auxiliares para procesar datos - CON CONVERSIÓN DE FECHAS
    @staticmethod
    def _convert_neo4j_datetime(value):
        if isinstance(value, DateTime):
            return value.to_native()
        return value

    @staticmethod
    def _process_record(record: dict) -> dict:
        processed = {}
        for key, value in record.items():
            processed[key] = OrdersController._convert_neo4j_datetime(value)
        return processed

    @staticmethod
    def _process_orders_data(orders_data: List[dict]) -> List[Dict[str, Any]]:
        if not orders_data:
            return []

        orders_dict = {}

        for record in orders_data:
            # Convertir tipos de Neo4j primero
            processed_record = OrdersController._process_record(record)

            order_id = processed_record.get("orden_id")

            if not order_id:
                continue  # Saltar registros sin order_id

            if order_id not in orders_dict:
                orders_dict[order_id] = {
                    "id": order_id,
                    "fecha": processed_record.get("fecha"),
                    "canal": processed_record.get("canal", "WEB"),
                    "moneda": processed_record.get("moneda"),
                    "total": processed_record.get("total"),
                    "cliente": {
                        "id": processed_record.get("cliente_id"),
                        "nombre": processed_record.get("cliente_nombre"),
                        "genero": processed_record.get("genero"),
                        "pais": processed_record.get("pais"),
                    },
                    "items": [],
                }

            # Agregar item a la order si existe producto_id
            if processed_record.get("producto_id"):
                item = {
                    "producto_id": processed_record.get("producto_id"),
                    "producto_nombre": processed_record.get("producto_nombre"),
                    "categoria_id": processed_record.get("categoria_id"),
                    "categoria": processed_record.get("categoria"),
                    "cantidad": processed_record.get("cantidad"),
                    "precio_unit": processed_record.get("precio_unit"),
                    "subtotal": processed_record.get("subtotal"),
                }
                orders_dict[order_id]["items"].append(item)

        return list(orders_dict.values())

    @staticmethod
    def _process_single_order_data(order_data: List[dict]) -> Dict[str, Any]:
        """Procesa los datos de una sola order"""
        if not order_data:
            return {}

        # Convertir todos los registros primero
        processed_data = [
            OrdersController._process_record(record) for record in order_data
        ]

        first_record = processed_data[0]
        order = {
            "id": first_record.get("orden_id"),
            "fecha": first_record.get("fecha"),
            "canal": first_record.get("canal", "WEB"),
            "moneda": first_record.get("moneda"),
            "total": first_record.get("total"),
            "cliente": {
                "id": first_record.get("cliente_id"),
                "nombre": first_record.get("cliente_nombre"),
                "genero": first_record.get("genero"),
                "pais": first_record.get("pais"),
            },
            "items": [],
        }

        for record in processed_data:
            if record.get("producto_id"):
                item = {
                    "producto_id": record.get("producto_id"),
                    "producto_nombre": record.get("producto_nombre"),
                    "categoria_id": record.get("categoria_id"),
                    "categoria": record.get("categoria"),
                    "cantidad": record.get("cantidad"),
                    "precio_unit": record.get("precio_unit"),
                    "subtotal": record.get("subtotal"),
                }
                order["items"].append(item)

        return order
