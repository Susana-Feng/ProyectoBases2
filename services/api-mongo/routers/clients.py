from typing import Any
from fastapi import APIRouter, status
from controllers.clients import ClientesController


router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/", summary="List clients")
def list_clientes(skip: int = 0, limit: int = 10) -> Any:
    return ClientesController.get_all_clientes(skip=skip, limit=limit)


@router.get("/{cliente_id}", summary="Get client by id")
def get_cliente(cliente_id: str) -> Any:
    return ClientesController.get_cliente_by_id(cliente_id)