from typing import List, Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
from repositories.orders import OrdenRepository
from schemas.orders import Orden

# module-level repo (same as current)
orden_repository = OrdenRepository()

class OrdersController:
    @staticmethod
    def get_all_orders(skip: int = 0, limit: int = 10):
        orders = orden_repository.get_all(skip=skip, limit=limit)
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
    def get_order_by_id(orden_id: str):
        order = orden_repository.get(orden_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Orden {orden_id} not found")
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
    def create_order(orden_data: Orden):
        orden_dict = orden_data.dict()
        orden_id = orden_repository.create(orden_dict)
        return {"orden_id": orden_id}

    @staticmethod
    def update_order(orden_id: str, orden_data: Orden):
        success = orden_repository.update(orden_id, orden_data.dict())
        if not success:
            raise HTTPException(status_code=404, detail=f"Orden {orden_id} not found")
        return {"message": "Orden updated"}

    @staticmethod
    def delete_order(orden_id: str):
        success = orden_repository.delete(orden_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Orden {orden_id} not found")
        return {"message": "Orden deleted"}