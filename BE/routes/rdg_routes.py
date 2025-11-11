from flask import Blueprint, request, jsonify
from services.rdg_runner import runner, RDGConfig

bp_rdg = Blueprint("rdg", __name__)

@bp_rdg.post("/start")
def rdg_start():
    data = request.get_json(silent=True) or {}
    try:
        cfg = RDGConfig(
            base_url=data.get("base_url", "http://127.0.0.1:5000"),
            rps=int(data.get("rps", 10)),
            concurrent=int(data.get("concurrent", 50)),
            active_dbms=data.get("active_dbms"),
            min_amount=int(data.get("min_amount", 1_000)),
            max_amount=int(data.get("max_amount", 100_000)),
            allow_same_db=bool(data.get("allow_same_db", False)),
        )
        runner.start(cfg)
        return jsonify(ok=True, status=runner.status())
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400

@bp_rdg.post("/stop")
def rdg_stop():
    runner.stop()
    return jsonify(ok=True, status=runner.status())

@bp_rdg.get("/status")
def rdg_status():
    return jsonify(ok=True, status=runner.status())
