# config/settings.py
import os
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

def _env(key: str, default: str | None = None) -> str:
    v = os.getenv(key)
    return v if v is not None else (default if default is not None else "")

def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default

def load_config(app) -> None:
    # BE 절대경로
    be_dir = Path(__file__).resolve().parents[1]  # /app/BE
    base_env = be_dir / ".env"
    load_dotenv(base_env)  # 공통

    profile = os.getenv("APP_PROFILE", "dev").strip().lower()
    prof_env = be_dir / f".env.{profile}"
    if prof_env.exists():
        load_dotenv(prof_env, override=True)

    app.config["PROFILE_INFO"] = {
        "profile": profile,
        "base_env": str(base_env if base_env.exists() else "(not found)"),
        "profile_env": str(prof_env if prof_env.exists() else "(not found)"),
    }

    # ───── 공통/플라스크 ─────
    app.config["DEBUG"] = _env("FLASK_ENV", "production") != "production"
    app.config["SECRET_KEY"] = _env("SECRET_KEY", "dev-secret")

    # ───── MySQL ─────
    # (.env.dev 기준 키: MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD)
    app.config["MYSQL"]: Dict[str, Any] = {
        "host": _env("MYSQL_HOST", "localhost"),
        "port": _env_int("MYSQL_PORT", 3306),
        "user": _env("MYSQL_USER", "root"),
        "password": _env("MYSQL_PASSWORD", ""),
        "db": _env("MYSQL_DB", ""),
        "charset": "utf8mb4",
    }

    # ───── PostgreSQL ─────
    # (.env.dev 기준 키: PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD)
    app.config["POSTGRES"]: Dict[str, Any] = {
        "host": _env("PG_HOST", "localhost"),
        "port": _env_int("PG_PORT", 5432),
        "user": _env("PG_USER", "postgres"),
        "password": _env("PG_PASSWORD", ""),
        "db": _env("PG_DB", "postgres"),
    }

    # ───── MongoDB ─────
    # (.env.dev 기준 키: MONGO_URL)  ← 기존 코드의 MONGO_URI로 매핑
    app.config["MONGO_URI"] = _env("MONGO_URL", "mongodb://localhost:27017/appdb")

        # ───── Oracle ─────
    # 우선 ORACLE_DSN이 있으면 그대로 사용 (SID/Service 자동 판별)
    oracle_dsn = _env("ORACLE_DSN", "").strip()

    if not oracle_dsn:
        # DSN이 없으면 HOST/PORT + SID 또는 SERVICE로 조립
        o_host = _env("ORACLE_HOST", "localhost")
        o_port = _env_int("ORACLE_PORT", 1521)
        o_sid = _env("ORACLE_SID", "").strip()
        o_service = _env("ORACLE_SERVICE", "").strip()

        if o_sid:                    # SID 방식: host:port:SID
            oracle_dsn = f"{o_host}:{o_port}:{o_sid}"
        elif o_service:              # Service 방식: host:port/service
            oracle_dsn = f"{o_host}:{o_port}/{o_service}"
        else:
            oracle_dsn = f"{o_host}:{o_port}/XE"  # 기본값

    app.config["ORACLE"]: Dict[str, Any] = {
        "dsn": oracle_dsn,
        "user": _env("ORACLE_USER", "system"),
        "password": _env("ORACLE_PASSWORD", "oracle"),
    }
