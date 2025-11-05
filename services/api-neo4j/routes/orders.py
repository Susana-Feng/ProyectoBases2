from typing import Any
from fastapi import APIRouter, status
from controllers.orders import OrdersController
from schemas.orders import Order

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/", summary="List all orders")
def list_orders() -> Any:
    return OrdersController.get_all_orders()

@router.get("/{order_id}", summary="Get order by ID")
def get_order(order_id: str) -> Any:
    return OrdersController.get_order_by_id(order_id)

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a new order")
def create_order(order: Order) -> Any:
    return OrdersController.create_order(order)

@router.put("/{order_id}", summary="Update an existing order")
def update_order(order_id: str, order: Order) -> Any:
    return OrdersController.update_order(order_id, order)

@router.delete("/{order_id}", summary="Delete an order")
def delete_order(order_id: str) -> Any:
    return OrdersController.delete_order(order_id)