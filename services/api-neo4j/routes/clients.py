from fastapi import APIRouter
from controllers.clients import ClientsController


router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", summary="List all clients")
def list_clients():
    return ClientsController.get_all_clients()