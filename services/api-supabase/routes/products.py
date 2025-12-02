from typing import Any
from fastapi import APIRouter, Query, Depends
from controllers.products import ProductsController
from config.database import get_mssql_connection
import pyodbc


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", summary="List all products")
def list_products() -> Any:
    return ProductsController.get_all_products()


@router.get("/by-skus")
async def get_consequents_by_skus_endpoint(
    skus: str = Query(..., description="Lista de SKUs separados por coma"),
    db_connection: pyodbc.Connection = Depends(get_mssql_connection),
) -> Any:
    # Convertir el string de SKUs separados por coma a lista
    skus_list = [sku.strip() for sku in skus.split(",") if sku.strip()]

    return ProductsController.get_consequents_by_skus(skus_list, db_connection)


@router.get("/by-codigos-supabase")
async def get_products_by_codigos_supabase_endpoint(
    skus: str = Query(..., description="Lista de SKUs basados en codigo supabase"),
    db_connection: pyodbc.Connection = Depends(get_mssql_connection),
) -> Any:
    # Convertir el string de SKUs separados por coma a lista
    skus_list = [sku.strip() for sku in skus.split(",") if sku.strip()]
    return ProductsController.get_skus_by_codes_supabase(skus_list, db_connection)
