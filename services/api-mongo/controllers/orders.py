from typing import List, Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
from repositories.orders import orderRepository
from schemas.orders import order

# module-level repo (same as current)
order_repository = orderRepository()

class OrdersController:
    @staticmethod
    def get_all_orders(skip: int = 0, limit: int = 10):
        orders = order_repository.get_all(skip=skip, limit=limit)
        total = len(orders)
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
        order_dict = order_data.dict()
        order_id = order_repository.create(order_dict)
        return {"order_id": order_id}

    @staticmethod
    def update_order(order_id: str, order_data: order):
        success = order_repository.update(order_id, order_data.dict())
        if not success:
            raise HTTPException(status_code=404, detail=f"order {order_id} not found")
        return {"message": "order updated"}

    @staticmethod
    def delete_order(order_id: str):
        success = order_repository.delete(order_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"order {order_id} not found")
        return {"message": "order deleted"}