from flask import Blueprint, request, jsonify

from ..querys.mongo_get_user_name import mongo_get_user_name

from common.error import generate_error_response
from common.success import generate_success_response

###############################################################################
# program ID : transactions.py
# 목적 : 이 프로그램에선 /mongo/ 로 들어오는 주소를 처리합니다.
# 설명 : Data는 mongo에서만 가져오고 처리합니다.
###############################################################################

mongo_transactions_bp = Blueprint("mongo_transactions", __name__)

# fun : mongo에서 사용자이름으로 사용자 데이터 조회
# GET
@mongo_transactions_bp.route("/user/<string:name>", methods=["GET"])
def get_username_mongo(name):
    ret = mongo_get_user_name(name)

    print(jsonify(ret))
    print("----------------------------------")

    if ret:
        return jsonify(ret)
    
    return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404

