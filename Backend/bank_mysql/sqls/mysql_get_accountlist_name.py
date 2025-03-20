from flask import Flask, jsonify
from ..db.mysql_connection import get_db_connection

# fun : MySQL에서 계좌이력 데이터 조회
# GET
# parms :
#        - name : 이름
def mysql_get_accountlist_id(acc_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT id,sender_id,receiver_id,amount,tranfer_type,transaction_date,status FROM transfer_list where sender_id like %s or receiver_id like %s order by id desc"
    cursor.execute(query,(acc_id,))  # 안전한 방식 (SQL Injection 방지)
    user = cursor.fetchall()

    cursor.close()
    conn.close()

    if user:
        return user
    else:
        return False
