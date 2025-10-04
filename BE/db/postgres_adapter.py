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
        
    def call_procedure(self, name: str, params=None):
        """CALL proc(…): 결과셋 없음(보통), rowcount만 의미 있음"""
        placeholders = ", ".join(["%s"] * len(params or ()))
        sql = f"CALL {name}({placeholders})"
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params or [])
            return {"rows_affected": cur.rowcount}

    def call_function(self, name: str, params=None):
        """SELECT * FROM func(…): 결과셋 반환"""
        placeholders = ", ".join(["%s"] * len(params or ()))
        sql = f"SELECT * FROM {name}({placeholders})"
        with self._conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or [])
            return cur.fetchall()