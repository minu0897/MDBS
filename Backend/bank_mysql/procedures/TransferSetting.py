from ..db.mysql_connection import get_db_connection

def transfersetting_mysql(list_id, code):
    #이체 확정 프로시저

    #list_id : 이체 id
    #code  : 이체 성공/실패 값
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print('======start========')
        print('id:transfersetting_mysql',)
        print('#parms',)
        print(' - list_id:',list_id)
        print(' - code:',code)
        print('===================')


        #PROCEDURE 실행
        cursor.execute("CALL TransferSetting(%s, %s)", (list_id, code))

        # 반환된 결과 집합 가져오기
        result = cursor.fetchone()  # { "status": -1 } 형태

        ##-아래 status는 procedure에서의 상태값-#
        #status:-1 이체시도조차x
        #status:2 성공
        #status:3 procedure error 관리자체크 필요
        #status:4 계좌조회실패
        #status:5 송금시 잔액부족
        conn.commit()
        return [result["status"]]
    
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cursor.close()
        conn.close()


