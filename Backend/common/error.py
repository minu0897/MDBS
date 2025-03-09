ERROR_CODES = {
    "INVALID_REQUEST": {"code": 1000, "message": "요청 값이 유효하지 않습니다."},
    "ACCOUNT_NOT_FOUND": {"code": 1001, "message": "없는 계좌"},
    "INSUFFICIENT_FUNDS": {"code": 1002, "message": "잔액 부족"},
    "INTERNAL_SERVER_ERROR": {"code": 1003, "message": "Server Error"},
    "DUPLICATE_TRANSACTION": {"code": 1004, "message": "이미 처리된 요청입니다."}
}

def generate_error_response(error_key, http_status=400):
    """오류 응답을 생성하는 함수"""
    error = ERROR_CODES.get(error_key, ERROR_CODES["INTERNAL_SERVER_ERROR"])
    return {"success": False, "error_code": error["code"], "error_message": error["message"]}, http_status
