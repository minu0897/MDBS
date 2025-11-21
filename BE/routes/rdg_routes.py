from flask import Blueprint, request, jsonify
from services.rdg_runner import runner, RDGConfig
import os

bp_rdg = Blueprint("rdg", __name__)

@bp_rdg.post("/start")
def rdg_start():
    data = request.get_json(silent=True) or {}
    try:
        # Password 검증
        password = data.get("password", "")
        RDG_PASSWORD = os.getenv("RDG_PASSWORD", "0897")
        if password != RDG_PASSWORD:
            return jsonify(ok=False, error="Invalid password"), 403

        # 현재 상태 확인 (디버깅용)
        current_status = runner.status()
        print(f"[RDG START] Current status before start: {current_status}")

        # 이미 실행 중이면 에러
        if current_status.get("running"):
            return jsonify(ok=False, error="RDG is already running"), 400

        cfg = RDGConfig(
            base_url=data.get("base_url", "http://127.0.0.1:5000"),
            rps=int(data.get("rps", 10)),
            concurrent=int(data.get("concurrent", 50)),
            active_dbms=data.get("active_dbms"),
            min_amount=int(data.get("min_amount", 1_000)),
            max_amount=int(data.get("max_amount", 100_000)),
            allow_same_db=bool(data.get("allow_same_db", False)),
            log_level=data.get("log_level", "DEBUG"),
        )
        runner.start(cfg)
        return jsonify(ok=True, status=runner.status())
    except Exception as e:
        print(f"[RDG START] Error: {e}")
        return jsonify(ok=False, error=str(e)), 400

@bp_rdg.post("/stop")
def rdg_stop():
    data = request.get_json(silent=True) or {}
    try:
        # Password 검증
        password = data.get("password", "")
        RDG_PASSWORD = os.getenv("RDG_PASSWORD", "0897")
        if password != RDG_PASSWORD:
            return jsonify(ok=False, error="Invalid password"), 403

        runner.stop()
        return jsonify(ok=True, status=runner.status())
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400

@bp_rdg.get("/status")
def rdg_status():
    return jsonify(ok=True, status=runner.status())
