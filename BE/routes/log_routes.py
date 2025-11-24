# routes/log_routes.py
from flask import Blueprint, send_file
from utils.response import ok, fail
from services.log_file_service import get_log_files, get_log_file_path

log_bp = Blueprint("log", __name__, url_prefix="/logs")

@log_bp.get("/list")
def list_logs():
    """
    로그 파일 목록 조회

    Returns:
        {
            "ok": true,
            "data": [
                {
                    "filename": "rdg_log_250124_143022.log",
                    "size": 1024000,
                    "modified": 1706083822.0
                },
                ...
            ]
        }
    """
    try:
        files = get_log_files()
        return ok(files)
    except Exception as e:
        return fail(str(e), 500)

@log_bp.get("/download/<filename>")
def download_log(filename: str):
    """
    로그 파일 다운로드

    Args:
        filename: 로그 파일명 (예: rdg_log_250124_143022.log)

    Returns:
        파일 다운로드 응답
    """
    try:
        file_path = get_log_file_path(filename)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype="text/plain"
        )
    except ValueError as e:
        return fail(str(e), 400)
    except Exception as e:
        return fail(str(e), 500)
