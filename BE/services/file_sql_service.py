# services/file_sql_service.py
import re, json
from pathlib import Path
from typing import Dict, Any, Tuple
from db.router import get_adapter

_BASE = Path(__file__).resolve().parent.parent / "sql"
_SELECT_RE = re.compile(r"^\s*select\b", re.I)

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
                meta[k] = v in ("1", "true", "True")
            elif k == "timeout_ms":
                try: meta[k] = int(v)
                except: pass
    return meta

def _load_sql(dbms: str, query_id: str) -> Tuple[str, Dict[str, Any]]:
    path = _BASE / dbms / f"{query_id}.sql"
    txt = path.read_text(encoding="utf-8")
    lines = txt.splitlines()
    meta = _parse_pragma(lines[0].strip()) if lines else {"timeout_ms":3000,"require_limit":False,"readonly":True}
    return txt, meta

def run_sql_file(dbms: str, query_id: str, params: Dict[str, Any]):
    dbms = dbms.lower()
    sql, meta = _load_sql(dbms, query_id)

    # 보호장치: readonly면 SELECT만 허용, LIMIT 요구 가능
    if meta.get("readonly", True) and not _SELECT_RE.match(sql):
        raise ValueError("readonly 템플릿은 SELECT만 허용됩니다.")
    if meta.get("require_limit", False) and "limit" not in sql.lower():
        raise ValueError("LIMIT 절이 필요합니다.")

    # 어댑터/타임아웃
    adapter = get_adapter(dbms)
    tms = int(meta.get("timeout_ms", 3000))
    try:
        if dbms == "postgres":
            adapter.execute_query(f"SET LOCAL statement_timeout = {tms}")
        elif dbms == "mysql":
            adapter.execute_query(f"SET SESSION MAX_EXECUTION_TIME={tms}")
        elif dbms == "oracle":
            # oracledb Thin: connection.callTimeout(ms) 를 어댑터에서 설정해도 OK
            pass
    except Exception:
        # 일부 드라이버/권한에서 set 실패 가능 → 무시하고 본문 실행
        pass

    return adapter.execute_query(sql, params or {})

def run_mongo_file(query_id: str, params: Dict[str, Any]):
    path = _BASE / "mongo" / f"{query_id}.json"
    s = path.read_text(encoding="utf-8")
    # 아주 단순한 %(name)s 치환 (안전 필요 시 단계적 생성 권장)
    for k, v in (params or {}).items():
        s = s.replace(f"%({k})s", str(v))
    low = s.lower()
    if "$where" in low or "$function" in low:
        raise ValueError("금지된 Mongo 연산자($where/$function)")
    pipeline = json.loads(s)
    mongo = get_adapter("mongo")
    return mongo.aggregate(path.stem, pipeline)  # 파일명=컬렉션 으로 쓰고 싶다면 이 줄 수정
