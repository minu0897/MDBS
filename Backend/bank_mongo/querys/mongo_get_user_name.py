from flask import Flask, jsonify
from ..db.mongo_connection import get_db_connection

# fun : mongo 사용자 데이터 조회 특정유저
# GET
# parms :
#        - name : 이름
def mongo_get_user_name(name):
    db = get_db_connection()
    collection = db["accounts"]  # 사용할 컬렉션 선택

    result = collection.find_one({"name": name})  #name에 해당하는 값 조회if data:
    result['_id'] = str(result['_id'])


    if result:
        return result
    else:
        return False