# routes/db_routes.py
from flask import Blueprint, request
from db.router import get_adapter
from utils.response import ok, fail

db_bp = Blueprint("db", __name__)

@db_bp.post("/query")
def run_query():
    """
    Body JSON:
    {
      "dbms": "mysql|postgres|oracle",
      "sql": "SELECT ...",
      "params": [ ... ]     # 또는 {"named": "params"}
    }
    """
    data = request.get_json(force=True) or {}
    try:
        dbms = data["dbms"]
        if dbms.lower() == "mongo":
            return fail("Mongo는 /db/mongo/* 엔드포인트를 사용하세요.", 400)
        adapter = get_adapter(dbms)
        res = adapter.execute_query(data["sql"], data.get("params"))
        return ok(res)
    except Exception as e:
        return fail(str(e), 400)

@db_bp.post("/procedure")
def run_procedure():
    """
    Body JSON:
    {
      "dbms": "mysql|postgres|oracle",
      "name": "proc_or_pkg.proc_name",
      "params": [ ... ]
    }
    """
    data = request.get_json(force=True) or {}
    try:
        dbms = data["dbms"]
        if dbms.lower() == "mongo":
            return fail("Mongo에는 프로시저 개념이 없습니다.", 400)
        adapter = get_adapter(dbms)
        res = adapter.call_procedure(data["name"], data.get("params"))
        return ok(res)
    except Exception as e:
        return fail(str(e), 400)

# --- Mongo 専用 ---
@db_bp.post("/mongo/find")
def mongo_find():
    """
    Body JSON:
    {
      "collection": "transactions",
      "query": {"field": "value"},
      "limit": 100
    }
    """
    data = request.get_json(force=True) or {}
    try:
        mongo = get_adapter("mongo")
        res = mongo.find(data["collection"], data.get("query"), data.get("limit", 100))
        return ok(res)
    except Exception as e:
        return fail(str(e), 400)

@db_bp.post("/mongo/aggregate")
def mongo_aggregate():
    """
    Body JSON:
    {
      "collection": "transactions",
      "pipeline": [ { "$match": {...} }, { "$group": {...}} ]
    }
    """
    data = request.get_json(force=True) or {}
    try:
        mongo = get_adapter("mongo")
        res = mongo.aggregate(data["collection"], data.get("pipeline", []))
        return ok(res)
    except Exception as e:
        return fail(str(e), 400)

@db_bp.post("/run_all")
def run_all():
    """
    Body JSON:
    {
      "ops": [
        {"dbms":"mysql","type":"query","sql":"SELECT NOW()"},
        {"dbms":"postgres","type":"procedure","name":"refresh_stats","params":[]},
        {"dbms":"oracle","type":"query","sql":"SELECT sysdate FROM dual"},
        {"dbms":"mongo","type":"find","collection":"transactions","query":{}, "limit": 3}
      ]
    }
    """
    data = request.get_json(force=True) or {}
    results = []
    for op in data.get("ops", []):
        try:
            dbms = op["dbms"].lower()
            if dbms == "mongo":
                mongo = get_adapter("mongo")
                typ = op.get("type", "find")
                if typ == "find":
                    out = mongo.find(op["collection"], op.get("query"), op.get("limit", 100))
                elif typ == "aggregate":
                    out = mongo.aggregate(op["collection"], op.get("pipeline", []))
                else:
                    raise ValueError(f"지원하지 않는 Mongo 타입: {typ}")
                results.append({"ok": True, "result": out})
            else:
                adapter = get_adapter(dbms)
                typ = op.get("type", "query")
                if typ == "query":
                    out = adapter.execute_query(op["sql"], op.get("params"))
                elif typ == "procedure":
                    out = adapter.call_procedure(op["name"], op.get("params"))
                else:
                    raise ValueError(f"지원하지 않는 타입: {typ}")
                results.append({"ok": True, "result": out})
        except Exception as e:
            results.append({"ok": False, "error": str(e)})
    return ok(results)
