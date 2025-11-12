from typing import List, Dict, Any
from pydantic import ValidationError
from fastapi import HTTPException
from schemas.orders import Order
from repositories.orders import OrderRepository
from neo4j.time import DateTime  # Importar el tipo de fecha de Neo4j

class OrdersController:
    
    @staticmethod
    def get_all_orders(skip: int = 0, limit: int = 10):
        try:
            # Validaciones básicas
            limit = min(limit, 100)  # evitar que pidan más de 100
            skip = max(skip, 0)

            # Leer datos paginados desde Neo4j
            orders_data = OrderRepository.read_orders(skip=skip, limit=limit)
            processed_orders = OrdersController._process_orders_data(orders_data)

            # Retornar resultado estructurado
            return {
                "skip": skip,
                "limit": limit,
                "count": len(processed_orders),
                "data": processed_orders
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving orders: {str(e)}")


    @staticmethod
    def get_order_by_id(order_id: str):
        try:
            order_data = OrderRepository.read_order_by_id(order_id)
            if not order_data:
                raise HTTPException(status_code=404, detail=f"order {order_id} not found")

            processed_order = OrdersController._process_single_order_data(order_data)
            return processed_order
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving order: {str(e)}")
        
    @staticmethod
    def _generate_order_id():
        """Genera un nuevo ID de orden automáticamente"""
        try:
            last_id = OrderRepository.get_last_order_id()
            print(f"Último ID encontrado: {last_id}")  # Debug
            
            if not last_id:
                return "O001"  # Primera orden
            
            # Extraer el número del último ID
            import re
            match = re.match(r"O(\d+)", last_id)
            if match:
                number = int(match.group(1))
                new_number = number + 1
                return f"O{new_number:03d}"  # Formato O001, O002, etc.
            else:
                # Si el formato no coincide, buscar el máximo numérico
                return "O001"
                
        except Exception as e:
            print(f"Error generando ID: {e}")
            return "O001"

    @staticmethod
    def _find_next_available_order_id(max_attempts=100):
        """Encuentra el próximo ID disponible verificando en la base de datos"""
        last_id = OrderRepository.get_last_order_id()
        
        if not last_id:
            return "O001"
        
        import re
        match = re.match(r"O(\d+)", last_id)
        if match:
            number = int(match.group(1))
            # Probar los siguientes N IDs
            for i in range(1, max_attempts + 1):
                potential_id = f"O{number + i:03d}"
                existing = OrderRepository.read_order_by_id(potential_id)
                if not existing:
                    return potential_id
        
        # Si no encuentra después de max_attempts, buscar desde el principio
        return OrdersController._find_first_available_gap(max_attempts)

    @staticmethod
    def create_order(order_data: Order):
        try:
            # Generar ID automáticamente
            auto_generated_id = OrdersController._find_next_available_order_id()
            print(f"ID generado: {auto_generated_id}")  # Debug
            
            # Preparar items para Neo4j
            items_for_neo4j = [
                {
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "precio_unit": item.precio_unit
                }
                for item in order_data.items
            ]
            
            # Crear la orden en la base de datos con el ID automático
            success = OrderRepository.create_order(
                id=auto_generated_id,
                cliente_id=order_data.cliente_id,
                fecha=order_data.fecha,
                canal=order_data.canal.value,
                moneda=order_data.moneda.value,
                total=order_data.total,
                items=items_for_neo4j
            )
            
            if success:
                return {
                    "orden_id": auto_generated_id,
                    "message": "Order created successfully"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create order in database")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

    @staticmethod
    def update_order(order_id: str, order_data: Order):
        try:
            # Verificar que la orden existe
            existing_order = OrderRepository.read_order_by_id(order_id)
            if not existing_order:
                raise HTTPException(status_code=404, detail=f"Orden {order_id} not found")
            
            # Preparar items para Neo4j
            items_for_neo4j = [
                {
                    "producto_id": item.producto_id,
                    "cantidad": item.cantidad,
                    "precio_unit": item.precio_unit
                }
                for item in order_data.items
            ]
            
            # Actualizar la orden - usar la versión corregida
            success = OrderRepository.update_order_with_relationships(
                
                id=order_id,
                fecha=order_data.fecha,
                canal=order_data.canal.value,
                cliente_id=order_data.cliente_id,
                moneda=order_data.moneda.value,
                total=order_data.total,
                items=items_for_neo4j
            )
            
            if success:
                return {"message": "Orden updated successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to update order in database")
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating order: {str(e)}")

    @staticmethod
    def delete_order(order_id: str):
        try:
            # Verificar que la order existe
            existing_order = OrderRepository.read_order_by_id(order_id)
            if not existing_order:
                raise HTTPException(status_code=404, detail=f"order {order_id} not found")
            
            OrderRepository.delete_order(order_id)
            return {"message": "order deleted"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")

    # Métodos auxiliares para procesar datos - CON CONVERSIÓN DE FECHAS
    @staticmethod
    def _convert_neo4j_datetime(value):
        if isinstance(value, DateTime):
            return value.to_native()
        return value

    @staticmethod
    def _process_record(record: dict) -> dict:
        processed = {}
        for key, value in record.items():
            processed[key] = OrdersController._convert_neo4j_datetime(value)
        return processed

    @staticmethod
    def _process_orders_data(orders_data: List[dict]) -> List[Dict[str, Any]]:
        if not orders_data:
            return []
            
        orders_dict = {}
        
        for record in orders_data:
            # Convertir tipos de Neo4j primero
            processed_record = OrdersController._process_record(record)
            
            order_id = processed_record.get('orden_id')
            
            if not order_id:
                continue  # Saltar registros sin order_id
                
            if order_id not in orders_dict:
                orders_dict[order_id] = {
                    'id': order_id,
                    'fecha': processed_record.get('fecha'),
                    'canal': processed_record.get('canal', 'WEB'),
                    'moneda': processed_record.get('moneda'),
                    'total': processed_record.get('total'),
                    'cliente': {
                        'id': processed_record.get('cliente_id'),
                        'nombre': processed_record.get('cliente_nombre'),
                        'genero': processed_record.get('genero'),
                        'pais': processed_record.get('pais')
                    },
                    'items': []
                }
            
            # Agregar item a la order si existe producto_id
            if processed_record.get('producto_id'):
                item = {
                    'producto_id': processed_record.get('producto_id'),
                    'producto_nombre': processed_record.get('producto_nombre'),
                    'categoria_id': processed_record.get('categoria_id'),
                    'categoria': processed_record.get('categoria'),
                    'cantidad': processed_record.get('cantidad'),
                    'precio_unit': processed_record.get('precio_unit'),
                    'subtotal': processed_record.get('subtotal')
                }
                orders_dict[order_id]['items'].append(item)
        
        return list(orders_dict.values())

    @staticmethod
    def _process_single_order_data(order_data: List[dict]) -> Dict[str, Any]:
        """Procesa los datos de una sola order"""
        if not order_data:
            return {}
        
        # Convertir todos los registros primero
        processed_data = [OrdersController._process_record(record) for record in order_data]
        
        first_record = processed_data[0]
        order = {
            'id': first_record.get('orden_id'),
            'fecha': first_record.get('fecha'),
            'canal': first_record.get('canal', 'WEB'),
            'moneda': first_record.get('moneda'),
            'total': first_record.get('total'),
            'cliente': {
                'id': first_record.get('cliente_id'),
                'nombre': first_record.get('cliente_nombre'),
                'genero': first_record.get('genero'),
                'pais': first_record.get('pais')
            },
            'items': []
        }
        
        for record in processed_data:
            if record.get('producto_id'):
                item = {
                    'producto_id': record.get('producto_id'),
                    'producto_nombre': record.get('producto_nombre'),
                    'categoria_id': record.get('categoria_id'),
                    'categoria': record.get('categoria'),
                    'cantidad': record.get('cantidad'),
                    'precio_unit': record.get('precio_unit'),
                    'subtotal': record.get('subtotal')
                }
                order['items'].append(item)
        
        return order