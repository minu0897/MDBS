# db/postgres_adapter.py
from typing import Any, Dict, Iterable, List, Optional, Union
import psycopg2
import psycopg2.extras

Params = Optional[Union[Iterable[Any], Dict[str, Any]]]

class PostgresAdapter:
    def __init__(self, cfg: Dict[str, Any]):
        """
        cfg 예: 
        { "host":"localhost","port":5432,"user":"postgres","password":"",
          "db":"postgres" }
        """
        self.cfg = cfg

    def _conn(self):
        return psycopg2.connect(
            host=self.cfg["host"],
            port=self.cfg["port"],
            user=self.cfg["user"],
            password=self.cfg["password"],
            dbname=self.cfg["db"],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )

    def execute_query(self, sql: str, params: Params = None):
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params or ())
            if cur.description:
                return cur.fetchall()
            return {"affected": cur.rowcount}

    def call_procedure(self, name: str, params: Optional[List[Any]] = None):
        """
        PostgreSQL 11+ 에서 CREATE PROCEDURE 사용 시: CALL proc(...)
        함수(RETURNING)가 아니라 프로시저일 때 이 경로 사용.
        """
        placeholders = ", ".join(["%s"] * (len(params or [])))
        sql = f"CALL {name}({placeholders});" if placeholders else f"CALL {name}();"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params or [])
            # CALL은 결과셋이 없으므로 상태만 반환
            return {"status": "ok"}
