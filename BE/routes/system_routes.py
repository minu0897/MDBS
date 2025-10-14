# routes/system_routes.py
import os
import subprocess
import psutil
import time
from flask import Blueprint, request
from utils.response import ok, fail

# docker stat server 전용
try:
    from services.docker_stats_service import collector as docker_collector  # 도커 DBMS들 상태
    _DOCKER_IMPORT_ERR = None
except Exception as e:
    docker_collector = None
    _DOCKER_IMPORT_ERR = e


sys_bp = Blueprint("system", __name__, url_prefix="/system") 

@sys_bp.get("/status")
def status():
    """
    서버 간단 상태값: CPU, 메모리, 디스크, loadavg
    """
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
    
# 처음 호출 시 수집기 시작, 캐시 반환
@sys_bp.get("/docker/stats")
def docker_stats():
    try:
        if os.getenv("APP_PROFILE", "dev").strip().lower() == 'dev':
            return ok({"age_sec": 111})

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

        # 즉시 1회 동기 수집 시도 (성공 시 즉시 실제 데이터 반환)
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
    """
    Body JSON:
    {
      "script": "demo_task.py",    # scripts/ 아래 파일명
      "args": ["--msg","hello"],
      "timeout": 60
    }
    """
    data = request.get_json(force=True) or {}
    script = data.get("script", "")
    args = [str(a) for a in data.get("args", [])]
    timeout = int(data.get("timeout", 60))
    try:
        cmd = ["python", os.path.join("scripts", script)] + args
        proc = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
        return ok({
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        })
    except Exception as e:
        return fail(str(e), 400)

@sys_bp.post("/exec")
def exec_cmd():
    """
    Body JSON:
    {
      "cmd": "ls",
      "args": ["-la","."],
      "timeout": 15
    }
    """
    data = request.get_json(force=True) or {}
    cmd = data.get("cmd", "")
    args = [str(a) for a in data.get("args", [])]
    timeout = int(data.get("timeout", 15))
    try:
        # 보안 제한 없음(개발용). 운영에선 화이트리스트/권한 필수.
        proc = subprocess.run([cmd] + args, timeout=timeout, capture_output=True, text=True)
        return ok({
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        })
    except Exception as e:
        return fail(str(e), 400)
