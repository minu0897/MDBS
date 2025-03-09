from flask import Flask, jsonify
from db.mysql_connection import get_db_connection

# fun : MySQL에서 사용자 데이터 조회
# GET
def get_username(name):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM accounts where name= %s"
    cursor.execute(query, (name,))  # 안전한 방식 (SQL Injection 방지)
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return jsonify(user)
    else:
        return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404
