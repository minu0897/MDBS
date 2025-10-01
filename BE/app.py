from flask import Flask, jsonify
from config.settings import load_config
from routes.db_routes import db_bp
from routes.system_routes import sys_bp
import os

os.environ["PYTHON_ORACLEDB_THIN"] = "1"     # 무조건 Thin
for k in ("ORACLE_HOME", "TNS_ADMIN", "TWO_TASK", "LOCAL"):
    os.environ.pop(k, None)                  # TNS/Thick 경로 강제 차단

def create_app():
    app = Flask(__name__)
    load_config(app)                       # .env → .env.{APP_PROFILE} 로드
    
    app.register_blueprint(db_bp,  url_prefix="/db")
    app.register_blueprint(sys_bp, url_prefix="/system")

    # ---- /healthz (liveness) ----
    @app.get("/healthz")
    def healthz():
        info = app.config.get("PROFILE_INFO", {})
        return jsonify({
            "status": "ok",
            "profile": info.get("profile"),
            "debug": app.config.get("DEBUG", False)
        }), 200
    
    if app.config.get("DEBUG"):   # dev에서만
        @app.get("/configz")
        def configz():
            c = app.config
            def pick(d, keys):
                return {k:d.get(k) for k in keys}
            return jsonify({
                "profile_info": c.get("PROFILE_INFO"),
                "mysql": pick(c.get("MYSQL", {}), ["host","port","db","user"]),
                "postgres": pick(c.get("POSTGRES", {}), ["host","port","db","user"]),
                "oracle": pick(c.get("ORACLE", {}), ["dsn","user"]),
                "mongo_uri": c.get("MONGO_URI"),
            })
    
    if app.config.get("DEBUG"):   # dev에서만
        @app.get("/diagz")
        def diagz():
            info = app.config.get("PROFILE_INFO", {})
            # oracledb import는 여기서(컨테이너에만 존재)
            thin = None
            try:
                import oracledb
                thin = bool(oracledb.is_thin_mode())
            except Exception:
                thin = "unavailable"

            return jsonify({
                "profile_info": info,
                "oracle": {
                    "dsn": app.config.get("ORACLE", {}).get("dsn"),
                    "user": app.config.get("ORACLE", {}).get("user"),
                },
                "env": {
                    "TNS_ADMIN": os.environ.get("TNS_ADMIN"),
                    "ORACLE_HOME": os.environ.get("ORACLE_HOME"),
                    "APP_PROFILE": os.environ.get("APP_PROFILE"),
                },
                "oracledb_thin_mode": thin,
            }), 200

    # 참고용 콘솔 로그
    info = app.config.get("PROFILE_INFO", {})
    print(f"[FLASK] profile={info.get('profile')} base={info.get('base_env')} prof={info.get('profile_env')}")
    print(f"[FLASK] DEBUG={app.config.get('DEBUG')}")

    return app

os.environ.pop("TNS_ADMIN", None)
os.environ.pop("ORACLE_HOME", None)

app = create_app()


if __name__ == "__main__":
    # 기본 포트 8000 (docker 포트 매핑과 맞추기)
    app.run(host="0.0.0.0", port=8000, debug=app.config.get("DEBUG", False))
