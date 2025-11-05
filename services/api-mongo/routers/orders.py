from typing import Any
from fastapi import APIRouter, status
from controllers.orders import OrdersController
from schemas.orders import order


router = APIRouter(prefix="/order", tags=["Order"])

@router.get("/", summary="List orders")
def list_orders(skip: int = 0, limit: int = 10) -> Any:
    return OrdersController.get_all_orders(skip=skip, limit=limit)


@router.get("/{order_id}", summary="Get order by id")
def get_order(order_id: str) -> Any:
    return OrdersController.get_order_by_id(order_id)


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create order")
def post_order(order: order) -> Any:
    return OrdersController.create_order(order)


@router.put("/{order_id}", summary="Update order")
def put_order(order_id: str, order: order) -> Any:
    return OrdersController.update_order(order_id, order)


@router.delete("/{order_id}", summary="Delete order")
def delete_order_route(order_id: str) -> Any:
    return OrdersController.delete_order(order_id)