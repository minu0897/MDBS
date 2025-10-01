# utils/response.py
from flask import jsonify

def ok(data, status: int = 200):
    """성공 응답 표준 포맷"""
    return jsonify({"ok": True, "data": data}), status

def fail(message: str, status: int = 400):
    """실패 응답 표준 포맷"""
    return jsonify({"ok": False, "error": message}), status
