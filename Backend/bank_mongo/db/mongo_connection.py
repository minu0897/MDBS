from pymongo import MongoClient
from bson import SON

from ..config import DB_CONFIG

def get_db_connection():
    """ Mongo 데이터베이스 연결 """

    # MongoDB 인증 정보
    MONGO_USER = DB_CONFIG["user"]
    MONGO_PASS = DB_CONFIG["password"]
    MONGO_HOST = DB_CONFIG["host"]
    MONGO_PORT = DB_CONFIG["port"]
    MONGO_DATABASE = DB_CONFIG["database"]

    # 연결 URI (인증 포함)
    mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}"
    
    try:
        client = MongoClient(mongo_uri)
        
        # MongoDB 서버 정보 가져오기 (연결 테스트)
        #server_info = client.server_info()  # 서버에 연결된 경우 서버 정보 반환
        #print(server_info)

        db = client[MONGO_DATABASE]
        return db
    except Exception as e:
        print("MongoDB 연결 실패:", str(e))
        return False