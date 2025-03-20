from flask import Flask, jsonify
from ..db.mysql_connection import get_db_connection

# fun : MySQL에서 계좌이력 데이터 조회
# GET
def mysql_get_accountlist_id(acc_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT id,sender_id,receiver_id,(-1)*amount,transaction_type,transaction_date,status,result_balance "
    query +="FROM transfer_list where sender_id = %s and status = 2 and transaction_type = 1 "
    query +="union all "
    query +="SELECT id,sender_id,receiver_id,amount,transaction_type,transaction_date,status,result_balance "
    query +="FROM transfer_list where receiver_id = %s and status = 2 and transaction_type = 2 "
    query +="order by transaction_date desc;"

    cursor.execute(query,(acc_id,acc_id))  # 안전한 방식 (SQL Injection 방지)
    user = cursor.fetchall()

    cursor.close()
    conn.close()

    if user:
        return user
    else:
        return False
