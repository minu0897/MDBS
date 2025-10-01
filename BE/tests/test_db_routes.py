# tests/test_db_routes.py
import json
import types
import pytest

from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

class _FakeRDBAdapter:
    def __init__(self, *a, **kw): pass
    def execute_query(self, sql, params=None):
        # 간단한 가짜 결과
        return [{"x": 1, "sql": sql}]
    def call_procedure(self, name, params=None):
        return {"called": name, "params": params or []}

class _FakeMongoAdapter:
    def __init__(self, *a, **kw): pass
    def find(self, collection, query=None, limit=100):
        return [{"_id": "1", "c": collection, "q": query or {}, "limit": limit}]
    def aggregate(self, collection, pipeline=None):
        return [{"_id": "g1", "count": 3}]

def _fake_get_adapter(dbms: str):
    d = dbms.lower()
    if d == "mongo":
        return _FakeMongoAdapter()
    return _FakeRDBAdapter()

def test_query_endpoint(client, monkeypatch):
    # db.router.get_adapter 를 Fake로 대체
    from db import router
    monkeypatch.setattr(router, "get_adapter", _fake_get_adapter)

    resp = client.post("/db/query", json={"dbms": "mysql", "sql": "SELECT 1"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert isinstance(data["data"], list)
    assert data["data"][0]["x"] == 1

def test_procedure_endpoint(client, monkeypatch):
    from db import router
    monkeypatch.setattr(router, "get_adapter", _fake_get_adapter)

    resp = client.post("/db/procedure", json={"dbms": "postgres", "name": "refresh_stats", "params": []})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["data"]["called"] == "refresh_stats"

def test_mongo_find_endpoint(client, monkeypatch):
    from db import router
    monkeypatch.setattr(router, "get_adapter", _fake_get_adapter)

    resp = client.post("/db/mongo/find", json={"collection": "transactions", "query": {"a": 1}, "limit": 2})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["data"][0]["c"] == "transactions"
    assert data["data"][0]["q"] == {"a": 1}
    assert data["data"][0]["limit"] == 2

def test_run_all_mixed(client, monkeypatch):
    from db import router
    monkeypatch.setattr(router, "get_adapter", _fake_get_adapter)

    payload = {
        "ops": [
            {"dbms": "mysql", "type": "query", "sql": "SELECT NOW()"},
            {"dbms": "postgres", "type": "procedure", "name": "do_it", "params": [1]},
            {"dbms": "mongo", "type": "find", "collection": "t", "query": {}, "limit": 1},
            {"dbms": "mongo", "type": "aggregate", "collection": "t", "pipeline": [{"$match": {}}]},
        ]
    }
    resp = client.post("/db/run_all", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    results = data["data"]
    assert len(results) == 4
    assert all("ok" in r for r in results)
