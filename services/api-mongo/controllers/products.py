from typing import List, Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
from repositories.products import ProductosRepository

# module-level repo (same as current)
productos_repository = ProductosRepository()

class ProductsController:
    @staticmethod
    def get_all_productos(skip: int = 0, limit: int = 10):
        productos = productos_repository.get_all(skip=skip, limit=limit)
        total = len(productos)
        # ensure any nested ObjectId values are converted to str
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        safe_productos = [_convert(doc) for doc in productos]
        return {"total": total, "skip": skip, "limit": limit, "data": safe_productos}

    @staticmethod
    def get_producto_by_id(producto_id: str):
        producto = productos_repository.get(producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {producto_id} not found")
        # convert nested ObjectId values if any
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        return _convert(producto)
