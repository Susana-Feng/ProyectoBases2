from datetime import datetime
from schemas.orders import Order, PaginationParams
from repositories.orders import OrderRepository
from pydantic import ValidationError


class OrdersController:

    @staticmethod
    def get_all_orders(offset: int = 0, limit: int = 10):
        try:
            orders = OrderRepository.get_orders(offset=offset, limit=limit)
            return orders
        except Exception as e:
            print("❌ Error en OrdersController.get_all_orders:", e)
            return {"error": str(e)}

    @staticmethod
    def create_order(order: Order):
        try:
        # Convertir objeto Order a dict
            order_dict = order.dict() 

            return OrderRepository.create_order(**order_dict)
        except ValidationError as ve:
            print("❌ Validation error in create_order:", ve.errors())
            return {"error": ve.errors()}
        except Exception as e:
            print("❌ Unexpected error in create_order:", e)
            return {"error": str(e)}

    @staticmethod
    def update_order(order_id: str, order_data: Order):
        try:
            return OrderRepository.update_order(**order_data.dict(), orden_id=order_id)
        except ValidationError as ve:
            print("❌ Validation error in update_order:", ve.errors())
            return {"error": ve.errors()}
        except Exception as e:
            print("❌ Unexpected error in update_order:", e)
            return {"error": str(e)}

    @staticmethod
    def delete_order(order_id: str):
        try:
            return OrderRepository.delete_order(order_id)
        except Exception as e:
            print("❌ Error in delete_order:", e)
            return {"error": str(e)}
