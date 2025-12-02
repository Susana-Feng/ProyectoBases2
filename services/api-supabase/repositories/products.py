from config.database import supabase
from typing import List, Optional, Dict, Any
import pyodbc
from bson.objectid import ObjectId
from bson.errors import InvalidId
from config.database import db

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

    
class productsRepository:
    
    @staticmethod
    def get_products():
        return get_products()
    
    @staticmethod
    def get_consequents_by_skus(db_connection: pyodbc.Connection, skus_list: str) -> List[Dict[str, Any]]:
        try:
            cursor = db_connection.cursor()
            print(f"Ejecutando stored procedure con SKUs: {skus_list}")
            # Ejecutar el stored procedure
            cursor.execute("EXEC dw.sp_obtener_consecuentes ?", skus_list)        
            # Obtener resultados
            rows = cursor.fetchall()
            # Convertir a lista de diccionarios
            rules = []
            for row in rows:
                rule = {
                    "Antecedent": row.Antecedent,
                    "Consequent": row.Consequent,
                    "Support": float(row.Support),
                    "Confidence": float(row.Confidence),
                    "Lift": float(row.Lift),
                    "SourceKeysAntecedentes": row.SourceKeysAntecedentes,
                    "SourceKeysConsecuentes": row.SourceKeysConsecuentes
                }
                rules.append(rule)    
            cursor.close()
            return rules
            
        except pyodbc.Error as e:
            raise Exception(f"Error ejecutando stored procedure: {str(e)}")
        except Exception as e:
            raise Exception(f"Error inesperado: {str(e)}")
        
    @staticmethod
    def get_skus_by_code_supabase(db_connection: pyodbc.Connection, codes_list: str) -> List[Dict[str, Any]]:
        try:
            cursor = db_connection.cursor()

            # Ejecutar el stored procedure
            cursor.execute("EXEC dw.sp_obtener_skus_por_codigo_supabase ?", codes_list)        
            # Obtener resultados
            rows = cursor.fetchall()
            # Convertir a lista de diccionarios
            rules = []
            for row in rows:
                rule = {
                    "SKU": row.SKU,
                    "CodigoSupabase": row.CodigoSupabase
                }
                rules.append(rule)    
            cursor.close()
            return rules
            
        except pyodbc.Error as e:
            raise Exception(f"Error ejecutando stored procedure: {str(e)}")
        except Exception as e:
            raise Exception(f"Error inesperado: {str(e)}")