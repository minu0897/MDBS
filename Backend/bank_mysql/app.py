from flask import Flask, jsonify
from db.mysql_connection import get_db_connection

app = Flask(__name__)

@app.route("/users", methods=["GET"])
def get_users():
    """ MySQL에서 사용자 데이터 조회 """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM accounts")
    users = cursor.fetchall()  # 조회 결과 가져오기

    cursor.close()
    conn.close()
    
    return jsonify(users)  # JSON 형태로 반환

if __name__ == "__main__":
    app.run(debug=True)
