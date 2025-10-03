# db/mysql_adapter.py
from typing import Any, Dict, Iterable, List, Optional, Union
import pymysql
import re

Params = Optional[Union[Iterable[Any], Dict[str, Any]]]

class MySQLAdapter:
    def __init__(self, cfg: Dict[str, Any]):
        """
        cfg 예:
        {
          "host":"localhost","port":3306,"user":"root","password":"",
          "db":"test","charset":"utf8mb4"
        }
        """
        self.cfg = cfg

    def _conn(self):
        return pymysql.connect(
            **self.cfg,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def execute_query(self, sql: str, params: Params = None):
        """
        SELECT/INSERT/UPDATE/DELETE 모두 처리.
        SELECT일 때 list[dict] 반환, 그 외에는 {"affected": n}
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params or ())
            if cur.description:  # SELECT 계열
                return cur.fetchall()
            return {"affected": cur.rowcount}

    def call_procedure(self, name: str, params: Optional[List[Any]] = None, out_count: int = 0):
        argv = list(params or [])

        # OUT 자리 자동 채우기 (끝에서 out_count개 None)
        if out_count > 0:
            need = out_count
            if len(argv) >= out_count:
                tail = argv[-out_count:]
                have = sum(1 for t in tail if t is None)
                need = out_count - have
            if need > 0:
                argv += [None] * need

        with self._conn() as conn, conn.cursor() as cur:
            cur.callproc(name, argv)

            # --- 첫 결과셋 잡기 (PyMySQL 방식) ---
            first_rs = None
            if cur.description:                 # 현재 커서가 결과셋을 가리키면
                first_rs = cur.fetchall()
            else:
                # 다음 결과셋으로 이동해가며 첫 결과셋 찾기
                while cur.nextset():
                    if cur.description:
                        first_rs = cur.fetchall()
                        break

            # --- OUT 읽기 ---
            out_vals = None
            if out_count > 0:
                var_base = re.sub(r"[^0-9A-Za-z_]", "_", name)  # MDBS.sp_x -> MDBS_sp_x
                start = len(argv) - out_count
                var_names = [f"@_{var_base}_{i}" for i in range(start, len(argv))]
                cur.execute("SELECT " + ", ".join(var_names))
                row = cur.fetchone()
                out_vals = {f"out{i}": row[var_names[i]] for i in range(out_count)}

            return {"resultset": first_rs, "out": out_vals}