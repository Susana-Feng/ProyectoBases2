from typing import Any
from fastapi import APIRouter
from controllers.clients import clientsController


router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", summary="List clients")
def list_clients() -> Any:
    return clientsController.get_all_clients()


@router.get("/{cliente_id}", summary="Get client by id")
def get_cliente(cliente_id: str) -> Any:
    return clientsController.get_cliente_by_id(cliente_id)
