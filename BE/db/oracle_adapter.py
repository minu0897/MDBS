# db/oracle_adapter.py
import os
os.environ["PYTHON_ORACLEDB_THIN"] = "1"     # 혹시 모를 순서 문제 방지
for k in ("ORACLE_HOME", "TNS_ADMIN", "TWO_TASK", "LOCAL"):
    os.environ.pop(k, None)

import oracledb

class OracleAdapter:
    def __init__(self, cfg):
        self.cfg = cfg

    def _normalize_dsn(self, dsn: str) -> str:
        s = (dsn or "").strip()
        # EZCONNECT(host:port/SERVICE | host:port:SID) 또는 (DESCRIPTION=...)만 허용
        if not s or (":" not in s and "/" not in s and "(" not in s):
            raise ValueError(
                f"Invalid DSN '{s}'. Use host:port/SERVICE or host:port:SID or (DESCRIPTION=...)"
            )
        return s

    def _conn(self):
        dsn = self._normalize_dsn(self.cfg["dsn"])
        conn = oracledb.connect(user=self.cfg["user"], password=self.cfg["password"], dsn=dsn)
        try:
            conn.callTimeout = 5000  # 쿼리 타임아웃(ms)
        except Exception:
            pass
        return conn

    def execute_query(self, sql, params=None):
        with self._conn() as cx, cx.cursor() as cur:
            cur.execute(sql, params or {})
            if cur.description:
                cols = [d[0].lower() for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
            return {"affected": cur.rowcount}

    def call_procedure(self, name, params=None):
        with self._conn() as cx, cx.cursor() as cur:
            res = cur.callproc(name, params or [])
            return {"result": list(res) if res is not None else None}
