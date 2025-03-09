from flask import Blueprint, request, jsonify
from procedures.ReceivableSetting import ReceivableSettingProcedure
from procedures.RemittanceSetting import RemittanceSettingProcedure
from procedures.TransferSetting import TransferSettingProcedure
from sqls.get_user import selectuser
from sqls.get_user_name import selectusername
from common.error import generate_error_response
from common.success import generate_success_response

mysql_transactions_bp = Blueprint("mysql_transactions", __name__)

# procedure : MySQL에서 이체 프로시저
# GET
@mysql_transactions_bp.route("/receive", methods=["POST"])
def transfer_mysql():
    data = request.json
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    amount = data.get("amount")

    if not sender_id or not receiver_id or not amount:
        return generate_error_response("INVALID_REQUEST", 400)

    status = ReceivableSettingProcedure(sender_id, receiver_id,amount)
    
    if status == "SUCCESS":
        ReceivableSettingProcedure(receiver_id,receiver_id, amount)
        return generate_success_response("TRANSACTION_SUCCESS", 200)
    elif status == "INSUFFICIENT_FUNDS":
        return generate_error_response("INSUFFICIENT_FUNDS", 400)
    else:
        return generate_error_response("INTERNAL_SERVER_ERROR", 500)
    
# fun : MySQL에서 사용자 데이터 조회
# GET
@mysql_transactions_bp.route("/users", methods=["GET"])
def get_users():
    ret = selectuser()
    return ret

# fun : MySQL에서 사용자이름으로 사용자 데이터 조회
# GET
@mysql_transactions_bp.route("/user/<string:name>", methods=["GET"])
def get_username(name):
    ret = selectusername(name)
    return ret