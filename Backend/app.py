from flask import Flask, jsonify
from bank_mysql.routes.transactions import mysql_transactions_bp
from bank_mysql.sqls.mysql_get_user import mysql_get_users
from bank_mysql.sqls.mysql_get_allbalance import mysql_get_allbalance
from bank_mysql.sqls.mysql_get_user_name import mysql_get_user_name
#from oracle.routes.transactions import oracle_transactions_bp
#from common.errors import generate_error_response
#from common.success import generate_success_response

app = Flask(__name__)
app.json.ensure_ascii = False  # 한글 깨짐 방지

# MySQL & Oracle API 엔드포인트 등록
app.register_blueprint(mysql_transactions_bp, url_prefix="/mysql")
#app.register_blueprint(oracle_transactions_bp, url_prefix="/oracle")


#  /users 엔드포인트: All DB에서 유저 목록을 가져와 합치기
@app.route("/users", methods=["GET"])
def get_all_users():
    try:
        mysql_users = mysql_get_users()# 리스트
        #oracle_users = get_oracle_users()

        #모든 유저
        all_users = mysql_users
        #all_users += oracle_users
        #all_users += mongo_users
        #all_users += postgre_user
        
        #총 금액
        mysql_balance = mysql_get_allbalance()[0]['bal']
        #mysql_balance = mysql_get_allbalance()
        
        all_balance = mysql_balance
        #all_balance += oracle_balance
        #all_balance += mongo_balance
        #all_balance += postgre_balance

        return jsonify({
            "balance":all_balance,
            "data": all_users
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#  /user/<string:name> 엔드포인트: All DB에서 유저 이름으로 검색
@app.route("/user/<string:name>", methods=["GET"])
def get_all_usersname(name):
    try:
        mysql_user = mysql_get_user_name(name)# 리스트

        if mysql_user:
            if len(mysql_user)>1:
                return jsonify({"error": "해당 이름을 가진사람이 2명이상입니다."}), 404
            return jsonify(mysql_user)
        

        return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)