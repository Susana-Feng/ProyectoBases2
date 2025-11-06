from datetime import datetime
from repositories.products import ProductRepository


class ProductsController:

    @staticmethod
    def get_all_products():
        try:
            products = ProductRepository.get_products()
            return products
        except Exception as e:
            print("❌ Error in controller (get_all_products):", e)
            return {"error": str(e)}