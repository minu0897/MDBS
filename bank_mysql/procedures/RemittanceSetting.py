from ..db.mysql_connection import get_db_connection

def remittancesetting_mysql(remittance_id, receivable_id,amount):
    #수금 준비 프로시저

    #remittance_id : 송금자 id
    #receivable_id : 수금자 id
    #amount        : 입금 금액
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print('======start========')
        print('id:remittancesetting_mysql',)
        print('#parms',)
        print(' - remittance_id:',remittance_id)
        print(' - receivable_id:',receivable_id)
        print(' - amount:',amount)
        print('===================')
        # 프로시저 호출 (OUT 파라미터 없이)
        cursor.execute("CALL RemittanceSetting(%s, %s, %s)", (remittance_id, receivable_id, amount))
        # 반환된 결과 집합 가져오기
        result = cursor.fetchone()  # { "create_id": 23, "status": "SUCCESS" } 형태
        conn.commit()
        print('======end==========')
        print(' - result:',result)
        print('===================')
        return [result["create_id"], result["status"]]
    except Exception as e:
        conn.rollback()
        return [str(e), None]
    finally:
        cursor.close()
        conn.close()
