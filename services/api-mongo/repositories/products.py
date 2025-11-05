from typing import List, Optional
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
    def get_all(skip: int = 0, limit: int = 10) -> List[dict]:
        products = []
        cursor = products_collection.find().skip(skip).limit(limit)
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            products.append(doc)
        return products
    

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