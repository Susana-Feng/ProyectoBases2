from typing import Any
from fastapi import APIRouter, status
from controllers.orders import OrdersController
from schemas.orders import Orden


router = APIRouter(prefix="/orden", tags=["Orden"])

@router.get("/", summary="List orders")
def list_orders(skip: int = 0, limit: int = 10) -> Any:
    return OrdersController.get_all_orders(skip=skip, limit=limit)


@router.get("/{orden_id}", summary="Get order by id")
def get_order(orden_id: str) -> Any:
    return OrdersController.get_order_by_id(orden_id)


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create order")
def post_order(orden: Orden) -> Any:
    return OrdersController.create_order(orden)


@router.put("/{orden_id}", summary="Update order")
def put_order(orden_id: str, orden: Orden) -> Any:
    return OrdersController.update_order(orden_id, orden)


@router.delete("/{orden_id}", summary="Delete order")
def delete_order_route(orden_id: str) -> Any:
    return OrdersController.delete_order(orden_id)