from datetime import datetime
from schemas.orders import Order
from repositories.orders import OrderRepository
from pydantic import ValidationError


class OrdersController:

    @staticmethod
    def get_all_orders():
        try:
            orders = OrderRepository.get_orders()
            return orders
        except Exception as e:
            print("❌ Error in controller (get_all_orders):", e)
            return {"error": str(e)}

    @staticmethod
    def create_order(order_data: dict):
        try:

            order = Order(**order_data)

            return OrderRepository.create_order(order_data)
        except ValidationError as ve:
            print("❌ Validation error in create_order:", ve.errors())
            return {"error": ve.errors()}
        except Exception as e:
            print("❌ Unexpected error in create_order:", e)
            return {"error": str(e)}

    @staticmethod
    def update_order(order_id: str, order_data: dict):
        try:
            order = Order(**order_data)
            return OrderRepository.update_order(order_data, order_id)
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
