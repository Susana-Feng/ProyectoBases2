from fastapi import HTTPException
from repositories.products import ProductRepository

class ProductsController:
    @staticmethod
    def get_all_products():
        try:
            data = ProductRepository.read_products()
            return {"total": len(data), "data": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")