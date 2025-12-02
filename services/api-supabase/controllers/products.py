from typing import Dict, List, Any
import pyodbc
from repositories.products import productsRepository

products_repository = productsRepository()


class ProductsController:
    @staticmethod
    def get_all_products():
        try:
            products = productsRepository.get_products()
            return products
        except Exception as e:
            print("❌ Error in controller (get_all_products):", e)
            return {"error": str(e)}

    @staticmethod
    def get_consequents_by_skus(
        skus: List[str], db_connection: pyodbc.Connection
    ) -> Dict[str, Any]:
        try:
            # Convertir lista de SKUs a string separado por comas
            skus_string = ",".join(skus)

            # Validación básica
            if not skus_string.strip():
                return {"rules": [], "count": 0}

            # Ejecutar stored procedure PASANDO ambos parámetros
            rules = products_repository.get_consequents_by_skus(
                db_connection, skus_string
            )

            return {"rules": rules, "count": len(rules)}

        except Exception as e:
            raise Exception(f"Error al obtener consecuentes: {str(e)}")

    @staticmethod
    def get_skus_by_codes_supabase(
        codes_supabase: List[str], db_connection: pyodbc.Connection
    ) -> Dict[str, Any]:
        try:
            # Convertir lista de codigos de supabase a string separado por comas
            codigos_string = ",".join(codes_supabase)

            # Validación básica
            if not codigos_string.strip():
                return {
                    "mappings": [],
                    "count": 0,
                }  # Corregido: retornar estructura consistente

            mappings = products_repository.get_skus_by_code_supabase(
                db_connection, codigos_string
            )

            return {"mappings": mappings, "count": len(mappings)}

        except Exception as e:
            raise Exception(f"Error al obtener SKUs: {str(e)}")
