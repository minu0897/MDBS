SUCCESS_CODES = {
    "TRANSACTION_SUCCESS": {"code": 2000, "message": "완료"}
}

def generate_success_response(success_key, http_status=200,arg=None):
    """성공 응답을 생성하는 함수"""
    success = SUCCESS_CODES.get(success_key, SUCCESS_CODES["TRANSACTION_SUCCESS"])
    return {"success": True, "success_code": success["code"], "message": success["message"],"parms":arg}, http_status
