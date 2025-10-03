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

    def call_procedure_with_cursor(self, name: str, params=None, out_spec=None):
        """
        out_spec 예: ["cursor", None, "cursor"]
          - "cursor"가 있는 위치는 OUT SYS_REFCURSOR 바인딩
          - None/생략은 IN 자리 (params의 값 사용)
        params는 IN 자리에 들어갈 값 배열(길이는 out_spec와 같거나 그보다 작아도 됨)
        반환: OUT 커서가 1개면 list[dict], 여러 개면 {"out0":[..], "out1":[..]}
        """
        params = list(params or [])
        with self._conn() as conn:
            conn.callTimeout = 5000
            with conn.cursor() as cur:
                bind_list = []
                out_positions = []
                out_spec = list(out_spec or [])
                # 각 인자 자리 매핑
                pi = 0  # params index
                for i, marker in enumerate(out_spec):
                    if marker == "cursor":
                        oc = conn.cursor()
                        bind_list.append(oc)
                        out_positions.append(i)
                    else:
                        # IN
                        bind_list.append(params[pi] if pi < len(params) else None)
                        pi += 1

                res = cur.callproc(name, bind_list)

                if not out_positions:
                    return {"rows_affected": cur.rowcount}

                outs = {}
                for idx, pos in enumerate(out_positions):
                    oc = res[pos]
                    cols = [d[0].lower() for d in oc.description]
                    outs[f"out{idx}"] = [dict(zip(cols, r)) for r in oc.fetchall()]

                return outs[next(iter(outs))] if len(outs) == 1 else outs