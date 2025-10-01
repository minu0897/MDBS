# db/mysql_adapter.py
from typing import Any, Dict, Iterable, List, Optional, Union
import pymysql

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

    def call_procedure(self, name: str, params: Optional[List[Any]] = None):
        """
        CALL proc_name(%s, %s, ...)
        OUT 파라미터가 있으면 드라이버 변수 사용이 필요하지만,
        기본 예시는 결과 셋(fetchall)만 반환.
        """
        with self._conn() as conn, conn.cursor() as cur:
            cur.callproc(name, params or [])
            # 일부 프로시저는 결과 셋을 반환하지 않을 수 있음
            try:
                rows = cur.fetchall()
            except Exception:
                rows = []
            return rows
