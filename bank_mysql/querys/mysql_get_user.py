from flask import Flask, jsonify
from ..db.mysql_connection import get_db_connection

# fun : MySQL에서 사용자 데이터 조회 모든 유저
# GET
# parms :
#        - name : 이름
def mysql_get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT CONCAT(LEFT(acc_id, 3), '-', SUBSTRING(acc_id, 4)) AS acc_id,balance,name,'mysql'as bank FROM accounts")
    users = cursor.fetchall()  # 조회 결과 가져오기

    cursor.close()
    conn.close()
    
    return users  # list형태로 반환