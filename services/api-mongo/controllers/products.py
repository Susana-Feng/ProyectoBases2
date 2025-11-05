from typing import List, Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
from repositories.products import productsRepository

# module-level repo (same as current)
products_repository = productsRepository()

class ProductsController:
    @staticmethod
    def get_all_products(skip: int = 0, limit: int = 10):
        products = products_repository.get_all(skip=skip, limit=limit)
        total = len(products)
        # ensure any nested ObjectId values are converted to str
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        safe_products = [_convert(doc) for doc in products]
        return {"total": total, "skip": skip, "limit": limit, "data": safe_products}

    @staticmethod
    def get_product_by_id(product_id: str):
        product = products_repository.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"product {product_id} not found")
        # convert nested ObjectId values if any
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        return _convert(product)
