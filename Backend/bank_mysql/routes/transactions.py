from flask import Blueprint, request, jsonify
from ..procedures.ReceivableSetting import receivablesetting_mysql
from ..procedures.RemittanceSetting import remittancesetting_mysql
from ..procedures.TransferSetting import transfersetting_mysql

from ..sqls.mysql_get_user import mysql_get_users
from ..sqls.mysql_get_user_name import mysql_get_user_name

from common.error import generate_error_response
from common.success import generate_success_response


mysql_transactions_bp = Blueprint("mysql_transactions", __name__)

# procedure : MySQL에서 이체 프로시저
# POST
@mysql_transactions_bp.route("/receive", methods=["POST"])
def receive_mysql():
    data = request.json
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    amount = data.get("amount")

    if not sender_id or not receiver_id or not amount:
        return generate_error_response("INVALID_REQUEST", 400)
    ret = receivablesetting_mysql(sender_id, receiver_id,amount)
    status = ret[1]#상태값
    if status == "SUCCESS":
        return generate_success_response("TRANSACTION_SUCCESS", 200)
    elif status == "INSUFFICIENT_FUNDS":#잔액부족
        return generate_error_response("INSUFFICIENT_FUNDS", 400)
    else:
        return generate_error_response("INTERNAL_SERVER_ERROR", 500)
    
# procedure : MySQL에서 이체 프로시저
# POST
@mysql_transactions_bp.route("/remittance", methods=["POST"])
def remittance_mysql():
    data = request.json
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    amount = data.get("amount")

    if not sender_id or not receiver_id or not amount:
        return generate_error_response("INVALID_REQUEST", 400)
    ret = remittancesetting_mysql(sender_id, receiver_id,amount)
    status = ret[1]#상태값
    if status == "SUCCESS":
        return generate_success_response("TRANSACTION_SUCCESS", 200)
    elif status == "INSUFFICIENT_FUNDS":#잔액부족
        return generate_error_response("INSUFFICIENT_FUNDS", 400)
    else:
        return generate_error_response("INTERNAL_SERVER_ERROR", 500)
    

# fun : MySQL에서 사용자 데이터 조회
# GET
@mysql_transactions_bp.route("/users", methods=["GET"])
def get_usersf():
    ret = jsonify(mysql_get_users())
    return ret

# fun : MySQL에서 사용자이름으로 사용자 데이터 조회
# GET
@mysql_transactions_bp.route("/user/<string:name>", methods=["GET"])
def get_username(name):
    ret = mysql_get_user_name(name)
    if ret:
        return jsonify(ret)
    
    
    #ret = oracle_get_user_name(name)
    #if ret:
    #    return jsonify(ret)
    
    return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404