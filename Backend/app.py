from flask import Flask
from bank_mysql.routes.transactions import mysql_transactions_bp
#from oracle.routes.transactions import oracle_transactions_bp
#from common.errors import generate_error_response
#from common.success import generate_success_response

app = Flask(__name__)
app.json.ensure_ascii = False  # 한글 깨짐 방지

# MySQL & Oracle API 엔드포인트 등록
app.register_blueprint(mysql_transactions_bp, url_prefix="/mysql")
#app.register_blueprint(oracle_transactions_bp, url_prefix="/oracle")

#
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
