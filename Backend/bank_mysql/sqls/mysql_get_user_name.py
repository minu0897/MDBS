from flask import Flask, jsonify
from ..db.mysql_connection import get_db_connection

# fun : MySQL에서 사용자 데이터 조회 특정유저
# GET
# parms :
#        - name : 이름
def mysql_get_user_name(name):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM accounts where name like %s"
    cursor.execute(query,(name,))  # 안전한 방식 (SQL Injection 방지)
    user = cursor.fetchall()

    cursor.close()
    conn.close()

    if user:
        return user
    else:
        return False
