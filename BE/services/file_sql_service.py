# services/file_sql_service.py
import re, json
from pathlib import Path
from typing import Dict, Any, Tuple, List
from db.router import get_adapter

# ───────────────────────── 공통 상수/정규식 ─────────────────────────
_BASE = Path(__file__).resolve().parent.parent / "sql"
_SELECT_RE = re.compile(r"^\s*select\b", re.I)
_ID_RE = re.compile(r"^[a-z0-9_.]+$")  # 파일 ID 화이트리스트
_FORBIDDEN_MONGO_OPS = {"$where", "$function"}

# ───────────────────────── 경로 유틸 ─────────────────────────
def _safe_path(dbms: str, qid: str, ext: str) -> Path:
    """
    파일 경로를 안전하게 생성(디렉터리 탈출 방지, 존재 확인).
    BE/sql/{dbms}/{qid}.{ext}
    """
    if not _ID_RE.match(qid or ""):
        raise ValueError("invalid id")
    base = (_BASE / dbms.lower()).resolve()
    p = (base / f"{qid}.{ext}").resolve()
    if not str(p).startswith(str(base)):
        raise ValueError("path traversal")
    if not p.exists():
        raise ValueError("file not found")
    return p

# ───────────────────────── SQL 프라그마 ─────────────────────────
def _parse_pragma(first_line: str) -> Dict[str, Any]:
    """
    SQL 첫 줄이 '-- key=val key2=val2' 형태면 파싱.
    예: -- timeout_ms=3000 require_limit=1 readonly=1
    """
    meta = {"timeout_ms": 3000, "require_limit": False, "readonly": True}
    if not first_line.startswith("--"):
        return meta
    parts = first_line[2:].strip().split()
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            k = k.strip(); v = v.strip()
            if k in ("require_limit", "readonly"):
                meta[k] = v.lower() in ("1", "true", "y", "yes")
            elif k == "timeout_ms":
                try: meta[k] = int(v)
                except: pass
    return meta

def _load_sql(dbms: str, query_id: str) -> Tuple[str, Dict[str, Any]]:
    path = _safe_path(dbms, query_id, "sql")
    txt = path.read_text(encoding="utf-8")
    lines = txt.splitlines()
    meta = _parse_pragma(lines[0].strip()) if lines else {"timeout_ms":3000,"require_limit":False,"readonly":True}
    return txt, meta

# ───────────────────────── SQL 실행 (RDB) ─────────────────────────
def run_sql_file(dbms: str, query_id: str, params: Dict[str, Any]):
    dbms = dbms.lower()
    sql, meta = _load_sql(dbms, query_id)

    # 보호장치: readonly면 SELECT만 허용
    if meta.get("readonly", True) and not _SELECT_RE.match(sql):
        raise ValueError("readonly 템플릿은 SELECT만 허용됩니다.")

    # LIMIT 요구: DBMS별로 체크(Oracle은 rownum / fetch first 인정)
    if meta.get("require_limit", False):
        lsql = sql.lower()
        has_limit = False
        if dbms in ("mysql", "postgres"):
            has_limit = " limit " in lsql
        elif dbms == "oracle":
            has_limit = (" rownum " in lsql) or (" fetch first " in lsql)
        if not has_limit:
            raise ValueError("LIMIT(또는 Oracle의 ROWNUM/FETCH FIRST) 절이 필요합니다.")

    # 어댑터/타임아웃
    adapter = get_adapter(dbms)
    tms = int(meta.get("timeout_ms", 3000))
    try:
        if dbms == "postgres":
            adapter.execute_query(f"SET LOCAL statement_timeout = {tms}")
        elif dbms == "mysql":
            adapter.execute_query(f"SET SESSION MAX_EXECUTION_TIME={tms}")
        # oracle은 adapter에서 conn.callTimeout을 설정할 수 있음
    except Exception:
        # 일부 드라이버/권한에서 set 실패 가능 → 무시하고 본문 실행
        pass

    return adapter.execute_query(sql, params or {})

# ───────────────────────── Mongo 유틸 ─────────────────────────
def _validate_pipeline(pipeline: Any) -> None:
    """각 stage는 dict 이고 키가 정확히 1개여야 하며, 위험 연산자를 금지."""
    if not isinstance(pipeline, list):
        raise ValueError("pipeline must be a list")
    for i, stage in enumerate(pipeline):
        if not isinstance(stage, dict) or len(stage) != 1:
            raise ValueError(f"stage #{i} must be an object with exactly one key")
        (op, _), = stage.items()
        if not isinstance(op, str) or not op.startswith("$"):
            raise ValueError(f"stage #{i} key must start with $")
        if op in _FORBIDDEN_MONGO_OPS:
            raise ValueError(f"forbidden operator: {op}")

def _clamp_int(v: Any, lo: int, hi: int) -> int:
    try:
        v = int(v)
    except Exception:
        v = lo
    return max(lo, min(v, hi))

def _force_limit(pipeline: List[dict], limit: int) -> List[dict]:
    """$limit 이 있으면 숫자로 덮어쓰고, 없으면 맨 끝에 추가."""
    out = []
    has_limit = False
    for st in pipeline:
        (op, val), = st.items()
        if op == "$limit":
            out.append({"$limit": int(limit)})
            has_limit = True
        else:
            out.append(st)
    if not has_limit:
        out.append({"$limit": int(limit)})
    return out

# ───────────────────────── Mongo 실행 ─────────────────────────
def run_mongo_file(collection: str, qid: str, params: dict):
    """
    파일(JSON) 실행 – aggregate pipeline 또는 operations 배열 지원

    Aggregate 예: { "collection":"accounts", "id":"query.accounts.list_all", "params":{"limit":100} }
    Operations 예: { "collection":"", "id":"reset.data_and_sequences", "params":{} }
    """
    path = _safe_path("mongo", qid, "json")
    txt = path.read_text(encoding="utf-8")
    data = json.loads(txt)

    mongo = get_adapter("mongo")

    # operations 형식: {"operations": [...]}
    if isinstance(data, dict) and "operations" in data:
        return _run_mongo_operations(mongo, data["operations"], params)

    # aggregate pipeline: [{"$match": {}}, ...]
    elif isinstance(data, list):
        _validate_pipeline(data)
        lim = _clamp_int((params or {}).get("limit", 100), 1, 1000)
        pipeline = _force_limit(data, lim)
        return mongo.aggregate(collection, pipeline, maxTimeMS=3000)

    raise ValueError("Invalid MongoDB file format")

def _run_mongo_operations(mongo, operations: List[dict], params: dict) -> dict:
    """
    MongoDB write operations 실행
    [
      {"type": "delete_many", "collection": "holds", "query": {}},
      {"type": "update_many", "collection": "accounts", "query": {}, "update": {"$set": {"balance": 0}}},
      {"type": "drop_collection", "collection": "transactions"}
    ]
    """
    results = []
    for i, op in enumerate(operations):
        op_type = op.get("type")
        coll = op.get("collection")

        if op_type == "delete_many":
            query = op.get("query", {})
            count = mongo.delete_many(coll, query)
            results.append({"operation": i, "type": op_type, "collection": coll, "deleted_count": count})

        elif op_type == "update_many":
            query = op.get("query", {})
            update = op.get("update", {})
            count = mongo.update_many(coll, query, update)
            results.append({"operation": i, "type": op_type, "collection": coll, "modified_count": count})

        elif op_type == "drop_collection":
            mongo.drop_collection(coll)
            results.append({"operation": i, "type": op_type, "collection": coll, "result": "dropped"})

        else:
            raise ValueError(f"Unsupported operation type: {op_type}")

    return {"executed": len(results), "results": results}
