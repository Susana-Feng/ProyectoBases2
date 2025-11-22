from typing import List, Optional, Dict, Any
import pyodbc
from bson.objectid import ObjectId
from bson.errors import InvalidId
from config.database import db

products_collection = db["productos"]

class productsRepository:

    @staticmethod
    def get(product_id: str) -> Optional[dict]:
        obj = _parse_objectid(product_id)
        if obj is None:
            return None
        data = products_collection.find_one({"_id": obj})
        if data:
            data["_id"] = str(data["_id"])
            return data
        return None

    @staticmethod
    def get_all(skip: int = 0, limit: int = 10000) -> List[dict]:
        products = []
        cursor = products_collection.find().skip(skip).limit(limit)
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            products.append(doc)
        return products

    @staticmethod
    def get_consequents_by_skus(db_connection: pyodbc.Connection, skus_list: str) -> List[Dict[str, Any]]:
        try:
            cursor = db_connection.cursor()
            print(f"Ejecutando stored procedure con SKUs: {skus_list}")
            # Ejecutar el stored procedure
            cursor.execute("EXEC dw.sp_obtener_consecuentes_por_skus ?", skus_list)        
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
    def get_skus_by_codigos_mongo(db_connection: pyodbc.Connection, skus_list: str) -> List[Dict[str, Any]]:
        try:
            cursor = db_connection.cursor()

            # Ejecutar el stored procedure
            cursor.execute("EXEC dw.sp_obtener_skus_por_codigos_mongo ?", skus_list)        
            # Obtener resultados
            rows = cursor.fetchall()
            # Convertir a lista de diccionarios
            rules = []
            for row in rows:
                rule = {
                    "SKU": row.SKU,
                    "CodigoMongo": row.CodigoMongo
                }
                rules.append(rule)    
            cursor.close()
            return rules
            
        except pyodbc.Error as e:
            raise Exception(f"Error ejecutando stored procedure: {str(e)}")
        except Exception as e:
            raise Exception(f"Error inesperado: {str(e)}")

def _parse_objectid(oid: str) -> Optional[ObjectId]:
    if not isinstance(oid, str):
        return None
    s = oid.strip()
    # strip wrapping single/double quotes if present
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        s = s[1:-1].strip()
    try:
        return ObjectId(s)
    except (InvalidId, TypeError):
        return None