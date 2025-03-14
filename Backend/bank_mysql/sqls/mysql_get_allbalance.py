from flask import Flask, jsonify
from ..db.mysql_connection import get_db_connection

# fun : MySQL에서 사용자 데이터 조회
# GET
# parms :
# 
def mysql_get_allbalance():
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT sum(balance)as bal FROM accounts")
    users = cursor.fetchall()  # 조회 결과 가져오기

    cursor.close()
    conn.close()
    
    return users  # list형태로 반환
