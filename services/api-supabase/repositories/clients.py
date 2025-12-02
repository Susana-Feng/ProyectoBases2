from config.database import supabase


def get_clients():
    try:
        response = supabase.table("cliente").select("*").execute()

        # .execute() devuelve un APIResponse con .data
        if not response.data:
            print("⚠️ No se encontraron clientes o hubo error")
            return []

        print("✅ Clientes:", response.data)
        return response.data

    except Exception as e:
        print("❌ Excepción al obtener clientes:", e)
        return None


class ClientRepository:
    @staticmethod
    def get_clients():
        return get_clients()
