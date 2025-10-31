from typing import List, Optional
from bson.objectid import ObjectId
from bson.errors import InvalidId
from config.database import db

ordenes_collection = db["ordenes"]


class OrdenRepository:
    @staticmethod
    def create(orden_data: dict) -> str:
        result = ordenes_collection.insert_one(orden_data)
        return str(result.inserted_id)

    @staticmethod
    def get(orden_id: str) -> Optional[dict]:
        obj = _parse_objectid(orden_id)
        if obj is None:
            return None
        data = ordenes_collection.find_one({"_id": obj})
        if data:
            data["_id"] = str(data["_id"])
            return data
        return None

    @staticmethod
    def get_all(skip: int = 0, limit: int = 10) -> List[dict]:
        orders = []
        cursor = ordenes_collection.find().skip(skip).limit(limit)
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            orders.append(doc)
        return orders
    
    @staticmethod
    def update(orden_id: str, update_data: dict) -> bool:
        obj = _parse_objectid(orden_id)
        if obj is None:
            return False
        result = ordenes_collection.update_one({"_id": obj}, {"$set": update_data})
        return result.modified_count > 0

    @staticmethod
    def delete(orden_id: str) -> bool:
        obj = _parse_objectid(orden_id)
        if obj is None:
            return False
        result = ordenes_collection.delete_one({"_id": obj})
        return result.deleted_count > 0

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