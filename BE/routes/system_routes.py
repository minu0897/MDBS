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
    _DOCKER_INIT_ERR = None
except Exception as e:
    docker_collector = None
    _DOCKER_INIT_ERR = e


sys_bp = Blueprint("system", __name__, url_prefix="/system") 

@sys_bp.get("/status")
def status():
    """
    서버 간단 상태값: CPU, 메모리, 디스크, loadavg
    """
    try:
        # dev 프로필이면 더미 응답
        if os.getenv("APP_PROFILE", "dev").strip().lower() == 'dev':
            return ok({"age_sec": 111})
        #  지연 import (부팅시 크래시 방지)
        global docker_collector, _DOCKER_INIT_ERR
        if docker_collector is None and _DOCKER_INIT_ERR is None:
            try:
                from services.docker_stats_service import collector as _collector
                docker_collector = _collector
            except Exception as e:
                _DOCKER_INIT_ERR = e
        if _DOCKER_INIT_ERR is not None:
            # 서비스 임포트 자체가 실패하면 앱은 살리고 JSON으로 알림
            return ok({"error": "docker_stats_import_failed", "detail": str(_DOCKER_INIT_ERR)})
        docker_collector.start_once()
        cache = docker_collector.get_cached()
        age = round(time.time() - (cache["ts"] or 0), 2)
        return ok({"age_sec": age, "containers": cache["data"]})
    except Exception as e:
        return fail(str(e), 500)
    
# 처음 호출 시 수집기 시작, 캐시 반환
@sys_bp.get("/docker/stats")
def docker_stats():
    """
    Docker 컨테이너 실시간 리소스: CPU%, MEM(bytes/limit/%), Net/Block IO 합산
    환경변수:
      - DOCKER_SOCK=unix://var/run/docker.sock
      - STATS_POLL_SEC=2
      - NAME_FILTER=mysql|postgres|oracle|mongo|mongod
      - LABEL_KEY=com.mdbs.role
      - LABEL_VAL=dbms
    """
    try:
        if os.getenv("APP_PROFILE", "dev").strip().lower() == 'dev':
            return ok({"age_sec": 111})
        else:
            docker_collector.start_once()
            cache = docker_collector.get_cached()
            age = round(time.time() - (cache["ts"] or 0), 2)
            return ok({"age_sec": age, "containers": cache["data"]})
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
