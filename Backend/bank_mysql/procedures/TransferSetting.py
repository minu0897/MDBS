from ..db.mysql_connection import get_db_connection

def transfersetting_mysql(list_id, code):
    #이체 확정 프로시저

        #list_id : 이체 id
        #status  : 이체 성공/실패 값

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        #status:2 성공
        #status:3 실패
        cursor.callproc("RemittanceSetting", (list_id, code, "@status"))
        cursor.execute("SELECT @status;")
        status = cursor.fetchone()["@status"]
        conn.commit()
        return status
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cursor.close()
        conn.close()
