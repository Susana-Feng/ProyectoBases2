from typing import Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
from bson.errors import InvalidId
from repositories.orders import orderRepository
from schemas.orders import order

# module-level repo (same as current)
order_repository = orderRepository()


class OrdersController:
    @staticmethod
    def _ensure_object_id(value: Any, field_name: str) -> BsonObjectId:
        """Convert string references into ObjectId or raise a validation error."""
        if isinstance(value, BsonObjectId):
            return value
        try:
            return BsonObjectId(str(value))
        except (InvalidId, TypeError):
            raise HTTPException(
                status_code=422,
                detail=f"{field_name} must be a valid ObjectId",
            ) from None

    @staticmethod
    def _prepare_payload(order_dict: dict) -> dict:
        """Ensure DB references inside the order use ObjectId values."""
        order_dict = dict(order_dict)
        order_dict["cliente_id"] = OrdersController._ensure_object_id(
            order_dict.get("cliente_id"), "cliente_id"
        )

        prepared_items = []
        for item in order_dict.get("items", []):
            item_copy = dict(item)
            item_copy["producto_id"] = OrdersController._ensure_object_id(
                item_copy.get("producto_id"), "items[].producto_id"
            )
            prepared_items.append(item_copy)
        order_dict["items"] = prepared_items
        return order_dict

    @staticmethod
    def get_all_orders(skip: int = 0, limit: int = 10):
        orders = order_repository.get_all(skip=skip, limit=limit)
        total = order_repository.count()

        # ensure any nested ObjectId values are converted to str
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        safe_orders = [_convert(doc) for doc in orders]
        return {"total": total, "skip": skip, "limit": limit, "data": safe_orders}

    @staticmethod
    def get_order_by_id(order_id: str):
        order = order_repository.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"order {order_id} not found")

        # convert nested ObjectId values if any
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        return _convert(order)

    @staticmethod
    def create_order(order_data: order):
        order_dict = OrdersController._prepare_payload(order_data.dict())
        order_id = order_repository.create(order_dict)
        return {"order_id": order_id}

    @staticmethod
    def update_order(order_id: str, order_data: order):
        order_dict = OrdersController._prepare_payload(order_data.dict())
        success = order_repository.update(order_id, order_dict)
        if not success:
            raise HTTPException(status_code=404, detail=f"order {order_id} not found")
        return {"message": "order updated"}

    @staticmethod
    def delete_order(order_id: str):
        success = order_repository.delete(order_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"order {order_id} not found")
        return {"message": "order deleted"}
