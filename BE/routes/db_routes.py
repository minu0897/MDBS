# BE/routes/db_routes.py
from flask import Blueprint, request
from utils.response import ok, fail
from services.file_sql_service import run_sql_file, run_mongo_file
from db.router import get_adapter

db_bp = Blueprint("db", __name__)

@db_bp.post("/file/sql")
def file_sql():
    """
    Body: {
      "dbms": "mysql|postgres|oracle",
      "id":   "query.accounts.list_all",
      "params": { "limit": 50, "offset": 0 }
    }
    -> 파일 규칙: BE/sql/{dbms}/{id}.sql
    """
    d = request.get_json(force=True) or {}
    
    try:
        res = run_sql_file(d["dbms"], d["id"], d.get("params", {}))
        return ok(res)
    except Exception as e:
        return fail(str(e), 400)

@db_bp.post("/file/mongo")
def file_mongo():
    d = request.get_json(force=True) or {}
    collection = d["collection"]          # ← 반드시 받기
    qid = d["id"]
    params = d.get("params", {})
    res = run_mongo_file(collection, qid, params)
    return ok(res)

@db_bp.post("/proc/exec")
def proc_exec():
    from utils.response import ok, fail
    from db.router import get_adapter
    try:
        d = request.get_json(force=True) or {}
        dbms = (d.get("dbms") or "").lower()
        name = d["name"]
        args = d.get("args", []) or []
        adapter = get_adapter(dbms)

        if dbms == "postgres":
            # FUNCTION 결과셋: SELECT * FROM func(...)
            # PROCEDURE: CALL proc(...)
            mode = (d.get("mode") or "proc").lower()
            if mode == "func":
                rows = adapter.call_function(name, args)
            else:
                rows = adapter.call_procedure(name, args)
            return ok(rows)

        if dbms == "oracle":
            # ★ 추가: out_count / out_types / timeout_ms 전달
            out_count  = int(d.get("out_count", 0))
            out_types  = d.get("out_types") or []

            out_spec = d.get("out")
            if out_spec:
                rows = adapter.call_procedure_with_cursor(name, args, out_spec=out_spec)
            else:
                rows = adapter.call_procedure(
                    name,
                    args,
                    out_count=out_count,
                    out_types=out_types
                )
            return ok(rows)
        if dbms == "mysql":
            out_count = int(d.get("out_count", 0))
            res = adapter.call_procedure(name, args, out_count=out_count)  # ← 반드시 전달
            return ok(res)

    except Exception as e:
        return fail(str(e), 400)
    