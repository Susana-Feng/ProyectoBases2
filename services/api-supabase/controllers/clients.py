from datetime import datetime
from repositories.clients import ClientRepository


class ClientsController:

    @staticmethod
    def get_all_clients():
        try:
            clients = ClientRepository.get_clients()
            return clients
        except Exception as e:
            print("❌ Error in controller (get_all_clients):", e)
            return {"error": str(e)}