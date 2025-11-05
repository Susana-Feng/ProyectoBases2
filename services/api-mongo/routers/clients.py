from typing import Any
from fastapi import APIRouter, status
from controllers.clients import clientsController


router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", summary="List clients")
def list_clients(skip: int = 0, limit: int = 10) -> Any:
    return clientsController.get_all_clients(skip=skip, limit=limit)


@router.get("/{cliente_id}", summary="Get client by id")
def get_cliente(cliente_id: str) -> Any:
    return clientsController.get_cliente_by_id(cliente_id)