from fastapi import APIRouter
from controllers.products import ProductsController

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", summary="List all products")
def list_products():
    return ProductsController.get_all_products()
