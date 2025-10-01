# BE/routes/db_routes.py
from flask import Blueprint, request
from utils.response import ok, fail
from services.file_sql_service import run_sql_file, run_mongo_file

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