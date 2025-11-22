# db/oracle_adapter.py
import os
import oracledb
from decimal import Decimal

os.environ["PYTHON_ORACLEDB_THIN"] = "1"     # 혹시 모를 순서 문제 방지
for k in ("ORACLE_HOME", "TNS_ADMIN", "TWO_TASK", "LOCAL"):
    os.environ.pop(k, None)


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
            conn.callTimeout = 60000  # 쿼리 타임아웃(ms) - 60초로 증가
        except Exception:
            pass
        return conn

    def execute_query(self, sql, params=None):
        with self._conn() as cx, cx.cursor() as cur:
            cur.execute(sql, params or {})
            if cur.description:                      # SELECT 등 결과셋
                cols = [d[0].lower() for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
            else:                                     # DML → 커밋 필요
                cx.commit()
                return {"affected": cur.rowcount}
        
    def call_procedure(self, name, params=None, out_count: int = 0, out_types: list[str] | None = None):
        """
        Oracle PROC 호출.
        - params: 전체 자리수만큼의 리스트 (OUT 자리는 placeholder로 None 넣어도 됨)
        - out_count: 끝에서부터 OUT 개수 (예: 2면 마지막 2개가 OUT)
        - out_types: ["number","varchar2", ...] (선택) OUT 타입 힌트
        반환 예:
          { "out": [12345, "1"], "all": [... 바인딩 최종값 ...] }
        """
        params = list(params or [])
        out_types = list(out_types or [])
        with self._conn() as cx, cx.cursor() as cur:
            binds = []
            created_out_vars_idx = []

            total = len(params)
            for i, a in enumerate(params):
                # OUT 범위면 변수 생성
                if out_count > 0 and i >= total - out_count:
                    j = i - (total - out_count)
                    hint = (out_types[j] if j < len(out_types) else "").lower()
                    if hint.startswith("varchar"):
                        v = cur.var(oracledb.DB_TYPE_VARCHAR)
                    elif hint in ("date", "timestamp"):
                        v = cur.var(oracledb.DB_TYPE_DATE)
                    else:
                        v = cur.var(oracledb.DB_TYPE_NUMBER)
                    binds.append(v)
                    created_out_vars_idx.append(i)
                else:
                    # IN 값 전처리(소수점 문자열은 Decimal로 캐스팅하면 안전)
                    if isinstance(a, str) and any(ch in a for ch in ('.', )):
                        try: a = Decimal(a)
                        except Exception: pass
                    binds.append(a)

            res = cur.callproc(name, binds)
            cx.commit() 
            # OUT 값만 추출
            outs = []
            for i in created_out_vars_idx:
                val = res[i]
                outs.append(val.getvalue() if hasattr(val, "getvalue") else val)

            # 전체 자리도 필요한 경우를 위해 반환
            def _val(x):
                return x.getvalue() if hasattr(x, "getvalue") else x

            return {"out": outs, "all": [ _val(x) for x in res ]}
        
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
                conn.commit() 

                if not out_positions:
                    return {"rows_affected": cur.rowcount}

                outs = {}
                for idx, pos in enumerate(out_positions):
                    oc = res[pos]
                    cols = [d[0].lower() for d in oc.description]
                    outs[f"out{idx}"] = [dict(zip(cols, r)) for r in oc.fetchall()]

                return outs[next(iter(outs))] if len(outs) == 1 else outs