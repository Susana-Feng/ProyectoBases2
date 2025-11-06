from typing import Any
from fastapi import APIRouter, status
from controllers.clients import ClientsController

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", summary="List all clients")
def list_orders() -> Any:
    return ClientsController.get_all_clients()
