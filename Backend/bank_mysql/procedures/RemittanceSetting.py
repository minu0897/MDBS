from ..db import mysql_connection

def remittancesetting_mysql(remittance_id, receivable_id,amount):
    #수금 준비 프로시저

    #remittance_id : 송금자 id
    #receivable_id : 수금자 id
    #amount        : 입금 금액
    conn = mysql_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc("ReceivableSetting", (remittance_id, receivable_id,amount, "@status"))
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
