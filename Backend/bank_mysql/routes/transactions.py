from flask import Blueprint, request, jsonify
from ..procedures.ReceivableSetting import receivablesetting_mysql
from ..procedures.RemittanceSetting import remittancesetting_mysql
from ..procedures.TransferSetting import transfersetting_mysql

from ..querys.mysql_get_user import mysql_get_users
from ..querys.mysql_get_user_name import mysql_get_user_name
from ..querys.mysql_get_accountlist_name import mysql_get_accountlist_name
from ..querys.mysql_get_accountlist_id import mysql_get_accountlist_id

from common.error import generate_error_response
from common.success import generate_success_response

###############################################################################
# program ID : transactions.py
# 목적 : 이 프로그램에선 /mysql/ 로 들어오는 주소를 처리합니다.
# 설명 : Data는 Mysql에서만 가져오고 처리합니다.
###############################################################################

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
        return generate_success_response("TRANSACTION_SUCCESS", 200,{"createId":ret[0]})
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
        return generate_success_response("TRANSACTION_SUCCESS", 200,{"createId":ret[0]})
    elif status == "INSUFFICIENT_FUNDS":#잔액부족
        return generate_error_response("INSUFFICIENT_FUNDS", 400)
    else:
        return generate_error_response("INTERNAL_SERVER_ERROR", 500)
    
# procedure : MySQL에서 이체 확정
# POST 
@mysql_transactions_bp.route("/transfer", methods=["POST"])
def transfer_mysql():
    data = request.json
    list_id = data.get("list_id")
    status = data.get("status")

    if not list_id or not status:
        return generate_error_response("INVALID_REQUEST", 400)
    

    ret = transfersetting_mysql(list_id, status)
    ##-아래 status는 procedure에서의 상태값-#
    #status:-1 이체시도조차( procedure실행은 했는데 아래코드가 안탐)
    #status:2 성공
    #status:3 procedure error 관리자체크 필요
    #status:4 계좌조회실패
    #status:5 송금시 잔액부족
    status = ret[0]#상태값
    print(status)
    if status == 2:
        return generate_success_response("TRANSACTION_SUCCESS", 200)
    elif status == -1:
        return generate_error_response("DB PROCEDURE ERROR", 500)
    elif status == 3:
        return generate_error_response("DB PROCEDURE ERROR", 500)
    elif status == 4:
        return generate_error_response("ACCOUNT_NOT_FOUND", 500)
    elif status == 5:
        return generate_error_response("INSUFFICIENT_FUNDS", 500)
    else:
        return generate_error_response("DB_PROCEDURE_ERROR", 500)
    

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


# fun : MySQL에서 사용자이름으로 이체내역 조회
# GET
@mysql_transactions_bp.route("/transferlist_name/<string:name>", methods=["GET"])
def get_transferlist_name(name):
    try:
        mysql_list = mysql_get_accountlist_name(name)# 리스트

        if mysql_list:
            return jsonify(mysql_list)
        

        return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
# fun : MySQL에서 계좌번호로 이체내역 조회
# GET
@mysql_transactions_bp.route("/transferlist_id/<string:name>", methods=["GET"])
def get_transferlist_id(id):
    try:
        mysql_list = mysql_get_accountlist_id(id)# 리스트

        if mysql_list:
            return jsonify(mysql_list)
        

        return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500