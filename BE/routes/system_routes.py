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