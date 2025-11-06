from typing import Any
from fastapi import APIRouter, status
from controllers.products import ProductsController

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/", summary="List all products")
def list_products() -> Any:
    return ProductsController.get_all_products()