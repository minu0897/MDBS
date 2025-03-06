import pymysql
from config import DB_CONFIG

def get_db_connection():
    """ MySQL 데이터베이스 연결 """
    return pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        cursorclass=pymysql.cursors.DictCursor  # 결과를 Dictionary 형태로 반환
    )
