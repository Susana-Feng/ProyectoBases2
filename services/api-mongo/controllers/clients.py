from typing import List, Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
from repositories.clients import ClientesRepository

# module-level repo (same as current)
clientes_repository = ClientesRepository()

class ClientesController:
    @staticmethod
    def get_all_clientes(skip: int = 0, limit: int = 10):
        clientes = clientes_repository.get_all(skip=skip, limit=limit)
        total = len(clientes)
        # ensure any nested ObjectId values are converted to str
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        safe_clientes = [_convert(doc) for doc in clientes]
        return {"total": total, "skip": skip, "limit": limit, "data": safe_clientes}

    @staticmethod
    def get_cliente_by_id(cliente_id: str):
        cliente = clientes_repository.get(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail=f"Cliente {cliente_id} not found")
        # convert nested ObjectId values if any
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        return _convert(cliente)
