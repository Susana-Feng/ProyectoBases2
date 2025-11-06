from config.database import supabase

def get_products():
    try:
        response = supabase.table("producto").select("*").execute()
        if not response.data:
            print("⚠️ No se encontraron productos o hubo error en la respuesta")
            return []

        print("✅ Productos:", response.data)
        return response.data

    except Exception as e:
        print("❌ Excepción al obtener productos:", e)
        return None

    
class ProductRepository:
    
    @staticmethod
    def get_products():
        return get_products()