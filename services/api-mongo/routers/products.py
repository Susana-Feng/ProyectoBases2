from typing import Any
from fastapi import APIRouter, status
from controllers.products import ProductsController


router = APIRouter(prefix="/productos", tags=["Productos"])

@router.get("/", summary="List products")
def list_productos(skip: int = 0, limit: int = 10) -> Any:
    return ProductsController.get_all_productos(skip=skip, limit=limit)


@router.get("/{producto_id}", summary="Get product by id")
def get_producto(producto_id: str) -> Any:
    return ProductsController.get_producto_by_id(producto_id)