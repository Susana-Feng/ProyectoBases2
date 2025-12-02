from typing import Any
from fastapi import APIRouter, status, Query
from controllers.orders import OrdersController
from schemas.orders import Order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", summary="List all orders with pagination")
def list_orders(
    offset: int = Query(0, description="Starting index of records (default: 0)"),
    limit: int = Query(10, description="Number of records to return (default: 10)"),
) -> Any:
    return OrdersController.get_all_orders(offset=offset, limit=limit)


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a new order")
def create_order(order: Order) -> Any:
    return OrdersController.create_order(order)


@router.put("/{order_id}", summary="Update an existing order")
def update_order(order_id: str, order: Order) -> Any:
    return OrdersController.update_order(order_id, order)


@router.delete("/{order_id}", summary="Delete an order")
def delete_order(order_id: str) -> Any:
    return OrdersController.delete_order(order_id)
