from typing import Dict, List, Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
import pyodbc
from repositories.products import productsRepository

# module-level repo (same as current)
products_repository = productsRepository()


class ProductsController:
    @staticmethod
    def get_all_products(skip: int = 0, limit: int = 10000):
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
            raise HTTPException(
                status_code=404, detail=f"product {product_id} not found"
            )

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

    @staticmethod
    def get_consequents_by_skus(
        skus: List[str], db_connection: pyodbc.Connection
    ) -> Dict[str, Any]:
        try:
            # Convertir lista de SKUs a string separado por comas
            skus_string = ",".join(skus)

            # Validación básica
            if not skus_string.strip():
                return {"rules": [], "count": 0}

            # Ejecutar stored procedure PASANDO ambos parámetros
            rules = products_repository.get_consequents_by_skus(
                db_connection, skus_string
            )

            return {"rules": rules, "count": len(rules)}

        except Exception as e:
            raise Exception(f"Error al obtener consecuentes: {str(e)}")

    @staticmethod
    def get_skus_by_codigos_mongo(
        codigos_mongo: List[str], db_connection: pyodbc.Connection
    ) -> Dict[str, Any]:
        try:
            # Convertir lista de códigos MongoDB a string separado por comas
            codigos_string = ",".join(codigos_mongo)

            # Validación básica
            if not codigos_string.strip():
                return {
                    "mappings": [],
                    "count": 0,
                }  # Corregido: retornar estructura consistente

            mappings = products_repository.get_skus_by_codigos_mongo(
                db_connection, codigos_string
            )

            return {"mappings": mappings, "count": len(mappings)}

        except Exception as e:
            raise Exception(f"Error al obtener SKUs: {str(e)}")
