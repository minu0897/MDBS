# db/mongo_adapter.py
from typing import Any, Dict, List, Optional, Union
from pymongo import MongoClient
from bson.decimal128 import Decimal128
from bson.objectid import ObjectId
from bson.binary import Binary
from bson.timestamp import Timestamp
import datetime as _dt
import base64

def _to_jsonable(x: Any) -> Any:
    """BSON -> JSON 직렬화 가능한 값으로 재귀 변환"""
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, Decimal128):
        # 손실 없이 내려주려면 문자열로. (필요시 float으로 바꿔도 됨)
        return str(x.to_decimal())
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, _dt.datetime):
        # timezone naive/aware 상관없이 ISO8601 문자열로
        return x.isoformat()
    if isinstance(x, Binary):
        return {"$binary": base64.b64encode(bytes(x)).decode("ascii")}
    if isinstance(x, Timestamp):
        return {"$timestamp": {"t": x.time, "i": x.inc}}
    if isinstance(x, dict):
        return {k: _to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_to_jsonable(v) for v in x]
    # 기타 알 수 없는 타입은 문자열로
    return str(x)

def _to_jsonable_list(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_to_jsonable(r) for r in rows]

class MongoAdapter:
    def __init__(self, cfg: Union[str, Dict[str, Any]]):
        """
        cfg: 문자열(URI) 또는 {"uri": "...", "db": "mdbs"}
        """
        if isinstance(cfg, str):
            uri = cfg
            db_name = None
        else:
            uri = cfg.get("uri") or cfg.get("url")
            db_name = cfg.get("db")

        if not uri:
            raise ValueError("Mongo URI is missing in config")

        self.client = MongoClient(uri)
        if db_name:
            self.db = self.client[db_name]
        else:
            # URI에 /dbname 이 포함돼 있어야 동작
            self.db = self.client.get_default_database()

    def find_one(self, collection: str, query: Dict[str, Any],
                 projection: Optional[Dict[str, int]] = None, **kwargs):
        doc = self.db[collection].find_one(query, projection, **kwargs)
        return _to_jsonable(doc) if doc is not None else None

    def find(self, collection: str, query: Dict[str, Any],
             projection: Optional[Dict[str, int]] = None,
             limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        cur = self.db[collection].find(query, projection, **kwargs).limit(int(limit))
        return _to_jsonable_list(list(cur))

    def aggregate(self, collection: str, pipeline: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        kwargs.setdefault("allowDiskUse", False)
        cur = self.db[collection].aggregate(pipeline, **kwargs)
        return _to_jsonable_list(list(cur))

    def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete multiple documents and return count of deleted documents"""
        result = self.db[collection].delete_many(query)
        return result.deleted_count

    def update_many(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update multiple documents and return count of modified documents"""
        result = self.db[collection].update_many(query, update)
        return result.modified_count

    def drop_collection(self, collection: str) -> None:
        """Drop entire collection (fast delete)"""
        self.db[collection].drop()
