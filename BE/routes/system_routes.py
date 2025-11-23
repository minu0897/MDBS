# routes/system_routes.py
import os
import subprocess
import psutil
import time
from flask import Blueprint, request
from utils.response import ok, fail

# 전역 상태
docker_collector = None
_DOCKER_IMPORT_ERR = None

sys_bp = Blueprint("system", __name__, url_prefix="/system")

@sys_bp.get("/status")
def status():
    try:
        v = psutil.virtual_memory()
        d = psutil.disk_usage("/")
        cpu = psutil.cpu_percent(interval=0.2)
        load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
        return ok({
            "cpu_percent": cpu,
            "mem": {"total": v.total, "used": v.used, "percent": v.percent},
            "disk": {"total": d.total, "used": d.used, "percent": d.percent},
            "loadavg": {"1m": load[0], "5m": load[1], "15m": load[2]},
        })
    except Exception as e:
        return fail(str(e), 500)

@sys_bp.get("/docker/stats")
def docker_stats():
    """
    Docker 컨테이너 리소스 즉시 1회 수집(가능하면) + 백그라운드 폴링 시작
    - APP_PROFILE=dev  : 더미 응답
    - APP_PROFILE=prod : 실제 수집
    """
    try:
        # 지연 import + 전역 상태 사용
        global docker_collector, _DOCKER_IMPORT_ERR
        if docker_collector is None and _DOCKER_IMPORT_ERR is None:
            try:
                from services.docker_stats_service import collector as _c
                docker_collector = _c
            except Exception as e:
                _DOCKER_IMPORT_ERR = e

        if _DOCKER_IMPORT_ERR is not None:
            return ok({"error": "docker_stats_import_failed", "detail": str(_DOCKER_IMPORT_ERR)})

        # 백그라운드 시작
        docker_collector.start_once()

        # 동기 1회 시도(성공 시 바로 실제 데이터 반환)
        try:
            docker_collector._ensure_client()
            rows = docker_collector._collect_once()
            return ok({"age_sec": 0, "containers": rows})
        except Exception as e:
            cache = docker_collector.get_cached()
            age = round(time.time() - (cache["ts"] or 0), 2)
            return ok({"age_sec": age, "containers": cache["data"], "detail": str(e)})

    except Exception as e:
        return fail(str(e), 500)

@sys_bp.post("/run-py")
def run_py():
    data = request.get_json(force=True) or {}
    script = data.get("script", "")
    args = [str(a) for a in data.get("args", [])]
    timeout = int(data.get("timeout", 60))
    try:
        cmd = ["python", os.path.join("scripts", script)] + args
        proc = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
        return ok({"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    except Exception as e:
        return fail(str(e), 400)

@sys_bp.post("/exec")
def exec_cmd():
    data = request.get_json(force=True) or {}
    cmd = data.get("cmd", "")
    args = [str(a) for a in data.get("args", [])]
    timeout = int(data.get("timeout", 15))
    try:
        proc = subprocess.run([cmd] + args, timeout=timeout, capture_output=True, text=True)
        return ok({"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    except Exception as e:
        return fail(str(e), 400)

@sys_bp.get("/conn-counts")
def db_conn_counts():
    from services.db_conn_count_service import get_all_dbms_session_counts as gather_conn_counts

    """
    각 DBMS 현재 커넥션 수 요약
    """
    try:
        data = gather_conn_counts()
        return ok(data)
    except Exception as e:
        return fail(str(e), 500)

@sys_bp.post("/reset")
def reset_environment():
    """
    시뮬레이션 환경 초기화 (Reset Environment)
    - 모든 DBMS의 트랜잭션 데이터 삭제 및 계정 잔액 초기화
    - Password 검증 필요
    - RDG 실행 중에는 차단

    Body: {"password": "your_password"}
    """
    from flask import current_app
    from services.rdg_runner import runner
    from db.router import get_adapter
    from services.mongo_tx_service import MongoTxService
    import oracledb

    try:
        data = request.get_json(force=True) or {}
        password = data.get("password", "")

        # 1. Password 검증
        RESET_PASSWORD = os.getenv("RESET_PASSWORD", "0897")
        if password != RESET_PASSWORD:
            return fail("Invalid password", 403)

        # 2. RDG 실행 상태 체크
        rdg_status = runner.status()
        if rdg_status.get("running"):
            return fail("Cannot reset while RDG is running. Please stop RDG first.", 400)

        # 3. 각 DBMS 리셋 실행
        results = {}
        errors = []

        # MySQL 리셋
        try:
            import pymysql
            mysql_adapter = get_adapter("mysql")
            reset_sql_path = os.path.join("sql", "mysql", "reset.data_and_sequences.sql")
            with open(reset_sql_path, "r", encoding="utf-8") as f:
                mysql_sql = f.read()

            # Multi-query 실행 (하나의 트랜잭션)
            mysql_adapter.execute_multi_query(mysql_sql)
            results["mysql"] = "OK"
        except pymysql.err.OperationalError as e:
            if "Lock wait timeout" in str(e):
                errors.append(f"MySQL: Tables are locked. Stop RDG first.")
                results["mysql"] = "FAILED: Tables are locked by ongoing transactions. Stop RDG and wait 5 seconds."
            else:
                errors.append(f"MySQL: {str(e)}")
                results["mysql"] = f"FAILED: {str(e)}"
        except Exception as e:
            errors.append(f"MySQL: {str(e)}")
            results["mysql"] = f"FAILED: {str(e)}"

        # PostgreSQL 리셋
        try:
            pg_adapter = get_adapter("postgres")
            reset_sql_path = os.path.join("sql", "postgres", "reset.data_and_sequences.sql")
            with open(reset_sql_path, "r", encoding="utf-8") as f:
                pg_sql = f.read()

            # PostgreSQL은 전체를 한 번에 실행 가능
            pg_adapter.execute_query(pg_sql)
            results["postgres"] = "OK"
        except Exception as e:
            errors.append(f"PostgreSQL: {str(e)}")
            results["postgres"] = f"FAILED: {str(e)}"

        # Oracle 리셋
        try:
            oracle_adapter = get_adapter("oracle")
            reset_sql_path = os.path.join("sql", "oracle", "reset.data_and_sequences.sql")
            with open(reset_sql_path, "r", encoding="utf-8") as f:
                oracle_sql = f.read()

            # Oracle은 PL/SQL 블록 또는 여러 문장일 수 있음
            # OracleAdapter는 pool이 없으므로 execute_query 사용
            oracle_adapter.execute_query(oracle_sql)
            results["oracle"] = "OK"
        except oracledb.Error as e:
            error_obj, = e.args
            if error_obj.code == 54:  # ORA-00054: resource busy
                errors.append(f"Oracle: Tables are locked. Stop RDG first.")
                results["oracle"] = "FAILED: Tables are locked by ongoing transactions. Stop RDG and wait 5 seconds."
            else:
                errors.append(f"Oracle: {str(e)}")
                results["oracle"] = f"FAILED: {str(e)}"
        except Exception as e:
            errors.append(f"Oracle: {str(e)}")
            results["oracle"] = f"FAILED: {str(e)}"

        # MongoDB 리셋
        try:
            from services.file_sql_service import run_mongo_file
            mongo_result = run_mongo_file("", "reset.data_and_sequences", {})
            results["mongo"] = "OK"
        except Exception as e:
            errors.append(f"MongoDB: {str(e)}")
            results["mongo"] = f"FAILED: {str(e)}"

        # 4. 결과 반환
        if errors:
            return ok({
                "success": False,
                "message": "Some databases failed to reset",
                "results": results,
                "errors": errors
            })
        else:
            return ok({
                "success": True,
                "message": "All databases reset successfully",
                "results": results
            })

    except Exception as e:
        return fail(str(e), 500)