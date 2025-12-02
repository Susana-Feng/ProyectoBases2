from typing import Any
from fastapi import APIRouter, Query, Depends
import pyodbc
from config.database import get_mssql_connection
from controllers.products import ProductsController


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", summary="List products")
def list_products(skip: int = 0, limit: int = 10000) -> Any:
    return ProductsController.get_all_products(skip=skip, limit=limit)


@router.get("/by-skus")
async def get_consequents_by_skus_endpoint(
    skus: str = Query(..., description="Lista de SKUs separados por coma"),
    db_connection: pyodbc.Connection = Depends(get_mssql_connection),
) -> Any:
    # Convertir el string de SKUs separados por coma a lista
    skus_list = [sku.strip() for sku in skus.split(",") if sku.strip()]

    return ProductsController.get_consequents_by_skus(skus_list, db_connection)


@router.get("/by-codigos-mongo")
async def get_products_by_codigos_mongo_endpoint(
    skus: str = Query(..., description="Lista de SKUs basados en codigo mongo"),
    db_connection: pyodbc.Connection = Depends(get_mssql_connection),
) -> Any:
    # Convertir el string de SKUs separados por coma a lista
    skus_list = [sku.strip() for sku in skus.split(",") if sku.strip()]
    return ProductsController.get_skus_by_codigos_mongo(skus_list, db_connection)


@router.get("/{product_id}", summary="Get product by id")
def get_product(product_id: str) -> Any:
    return ProductsController.get_product_by_id(product_id)
