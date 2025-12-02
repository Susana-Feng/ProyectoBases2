from typing import Any
from fastapi import HTTPException
from bson import ObjectId as BsonObjectId
from repositories.clients import clientsRepository

# module-level repo (same as current)
clients_repository = clientsRepository()


class clientsController:
    @staticmethod
    def get_all_clients():
        clients = clients_repository.get_all()
        total = len(clients)

        # ensure any nested ObjectId values are converted to str
        def _convert(o: Any):
            if isinstance(o, BsonObjectId):
                return str(o)
            if isinstance(o, dict):
                return {k: _convert(v) for k, v in o.items()}
            if isinstance(o, list):
                return [_convert(v) for v in o]
            return o

        safe_clients = [_convert(doc) for doc in clients]
        return {"total": total, "skip": 0, "limit": 0, "data": safe_clients}

    @staticmethod
    def get_cliente_by_id(cliente_id: str):
        cliente = clients_repository.get(cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=404, detail=f"Cliente {cliente_id} not found"
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

        return _convert(cliente)
