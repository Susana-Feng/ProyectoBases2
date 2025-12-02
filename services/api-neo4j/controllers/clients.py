from fastapi import HTTPException
from repositories.clients import ClientRepository


class ClientsController:
    @staticmethod
    def get_all_clients():
        try:
            data = ClientRepository.read_clients()
            return {"total": len(data), "data": data}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error retrieving clients: {str(e)}"
            )
