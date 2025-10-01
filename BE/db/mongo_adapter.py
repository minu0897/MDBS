
    




# db/mongo_adapter.py
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from bson import ObjectId

class MongoAdapter:
    def __init__(self, uri: str):
        """
        uri 예: "mongodb://user:pw@localhost:27017/appdb"
        get_default_database()로 DB 바인딩됨.
        """
        self.client = MongoClient(uri)
        self.db = self.client.get_default_database()

    def find(self, collection: str, query: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
        docs = list(self.db[collection].find(query or {}).limit(int(limit)))
        for d in docs:
            if isinstance(d.get("_id"), ObjectId):
                d["_id"] = str(d["_id"])
        return docs

    def aggregate(self, collection: str, pipeline: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        docs = list(self.db[collection].aggregate(pipeline or []))
        for d in docs:
            if "_id" in d and isinstance(d["_id"], ObjectId):
                d["_id"] = str(d["_id"])
        return docs
