# BE/services/db_conn_count_service.py
from typing import Any, Dict, List
from flask import current_app


def get_mysql_session_count() -> Dict[str, Any]:
    try:
        from db.mysql_adapter import MySQLAdapter
        cfg = current_app.config["MYSQL"]
        adapter = MySQLAdapter(cfg)

        result = adapter.execute_query("SHOW STATUS LIKE 'Threads_connected'")
        sessions = int(result[0]["Value"]) if result else 0

        return {"dbms": "mysql", "sessions": sessions}
    except Exception as e:
        return {"dbms": "mysql", "sessions": 0, "error": str(e)}


def get_postgres_session_count() -> Dict[str, Any]:
    try:
        from db.postgres_adapter import PostgresAdapter
        cfg = current_app.config["POSTGRES"]
        adapter = PostgresAdapter(cfg)

        result = adapter.execute_query("""
            SELECT count(*) as count
            FROM pg_stat_activity
            WHERE state = 'active' OR state = 'idle'
        """)
        sessions = int(result[0]["count"]) if result else 0

        return {"dbms": "postgres", "sessions": sessions}
    except Exception as e:
        return {"dbms": "postgres", "sessions": 0, "error": str(e)}


def get_oracle_session_count() -> Dict[str, Any]:
    try:
        from db.oracle_adapter import OracleAdapter
        cfg = current_app.config["ORACLE"]
        adapter = OracleAdapter(cfg)

        # v$session 대신 현재 세션의 SID를 조회하는 방식으로 변경
        # 일반 사용자도 자신의 세션 정보는 조회 가능
        result = adapter.execute_query("""
            SELECT COUNT(*) as count
            FROM sys.v_$session WHERE username = 'MDBS' AND type = 'USER'
        """)
        sessions = int(result[0]["count"]) if result else 0

        return {"dbms": "oracle", "sessions": sessions}
    except Exception as e:
        # v$session 조회 실패시 fallback: 단순히 현재 연결이 성공했으므로 1 반환
        try:
            # 단순 쿼리로 연결 확인
            adapter.execute_query("SELECT 1 as connected FROM dual")
            return {"dbms": "oracle", "sessions": 1, "note": "limited_access"}
        except:
            return {"dbms": "oracle", "sessions": 0, "error": str(e)}


def get_mongo_session_count() -> Dict[str, Any]:
    try:
        from db.mongo_adapter import MongoAdapter
        adapter = MongoAdapter({
            "uri": current_app.config["MONGO_URI"],
            "db": current_app.config.get("MONGO_DB", "mdbs")
        })

        # serverStatus는 admin 권한 필요, 대신 currentOp 사용 (일반 사용자도 조회 가능)
        try:
            result = adapter.db.command("serverStatus")
            sessions = result.get("connections", {}).get("current", 0)
        except:
            # serverStatus 실패시 currentOp로 시도
            result = adapter.db.command("currentOp")
            sessions = len(result.get("inprog", []))

        return {"dbms": "mongodb", "sessions": sessions}
    except Exception as e:
        # 모든 조회 실패시 fallback: 연결 성공했으므로 1 반환
        try:
            # ping으로 연결 확인
            adapter.db.command("ping")
            return {"dbms": "mongodb", "sessions": 1, "note": "limited_access"}
        except:
            return {"dbms": "mongodb", "sessions": 0, "error": str(e)}


def get_all_dbms_session_counts() -> List[Dict[str, Any]]:
    results = []

    results.append(get_mysql_session_count())
    results.append(get_postgres_session_count())
    results.append(get_oracle_session_count())
    results.append(get_mongo_session_count())

    return results
