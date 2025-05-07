#Random Data Generator Python file
import asyncio
import aiohttp
import csv
import random
import logging
import json
import time



import sys
sys.path.append('./Backend/common/config') 
from RDGconfig import RDG_CONFIG
from Flaskconfig import FLASK_CONFIG

serverurl = FLASK_CONFIG["SERVERIP"]+":"+FLASK_CONFIG["SERVERPORT"]



# 로그 파일과 로그 레벨 설정
logging.basicConfig(
    filename='app.log',  # 로그 파일 이름
    level=logging.DEBUG,  # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # 로그 메시지 형식
    encoding='utf-8'  # 한글을 제대로 출력하기 위한 UTF-8 인코딩
)

# 로그 핸들러 설정 (파일 핸들러)
file_handler = logging.FileHandler('app.log', mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 예시 로그
#logging.debug("디버그 메시지")
#logging.info("정보 메시지")
#logging.warning("경고 메시지")
#logging.error("에러 메시지")
#logging.critical("치명적인 에러 메시지")

peoples=[]
dataCount=RDG_CONFIG["DATA_COUNT"]#현재까지 실제DB에 있는 data의 갯수

        

async def call_api(session, url, data):
    """
    주어진 URL에 POST 요청을 보내고, 결과 JSON을 반환하는 함수.
    """
    try:
        async with session.post(url, json=data) as response:
            result = await response.json()
            #print(data)
            #print(f"[{time.strftime('%X')}] {url} 호출 성공: {result}")
            return result
    except Exception as e:
        #print(f"[{time.strftime('%X')}] {url} 호출 에러: {e}")
        return None

async def process_chain(session, data):
    """
    체인 방식으로 API를 호출하는 함수.
    """
    logging.debug(f"TaskID : {data['task_id']} >>>> ===0. 시작===")

    remittancebank=data["sender_id"][0:3]
    receivebank=data["receiver_id"][0:3]
    
    logging.info(f" TaskID : {data['task_id']} >>>> 보내는사람   : {data['sender_id']}")
    logging.info(f" TaskID : {data['task_id']} >>>> 받는사람     : {data['receiver_id']}")
    logging.info(f" TaskID : {data['task_id']} >>>> 금액         : {data['amount']}")


    #보내는 쪽 DB
    if remittancebank == "001":
        remittancebank='mysql'
    elif remittancebank == "002":
        remittancebank='oracle'
    elif remittancebank == "003":
        remittancebank='mongo'
    elif remittancebank == "004":
        remittancebank='postgre'

    #받는 쪽 DB
    if receivebank == "001":
        receivebank='mysql'
    elif receivebank == "002":
        receivebank='oracle'
    elif receivebank == "003":
        receivebank='mongo'
    elif receivebank == "004":
        receivebank='postgre'

    # 1. 송금 API 호출
    logging.debug(f"TaskID : {data['task_id']} >>>> ===1. 송금 API 시작===")
    #ex) http://127.0.0.1:5000/mysql/remittance
    url_remittance = "http://"+serverurl+"/"+remittancebank+"/remittance"
    resultremittance = await call_api(session, url_remittance, data)
    if not resultremittance or resultremittance.get("success_code") != 2000:
        logging.error(f"TaskID : {data['task_id']} >>>> 송금 대기 실패 API 실패: "+json.dumps(resultremittance, ensure_ascii=False))
        logging.debug(f"TaskID : {data['task_id']} >>>> ===이체 실패===")
        return
    remittance_create_id = resultremittance.get("parms")["createId"]

    # 2. 수금 API 호출
    logging.debug(f"TaskID : {data['task_id']} >>>> ===2. 수금 API 시작===")
    #ex) http://127.0.0.1:5000/mysql/receive
    url_receive = "http://"+serverurl+"/"+receivebank+"/receive"
    resultreceive = await call_api(session, url_receive, data)
    if not resultreceive or resultreceive.get("success_code") != 2000:
        logging.error(f"TaskID : {data['task_id']} >>>> 수금 대기 실패 API 실패: "+json.dumps(resultreceive, ensure_ascii=False))
        logging.debug(f"TaskID : {data['task_id']} >>>> ===이체 실패===")
        return
    receive_create_id = resultreceive.get("parms")["createId"]

    # 3. 송금 확정 API
    logging.debug(f"TaskID : {data['task_id']} >>>> ===3. 송금 확정 API 시작===")
    logging.info(f" TaskID : {data['task_id']} >>>> Create ID  : {remittance_create_id}")
    url_transfer = "http://"+serverurl+"/"+remittancebank+"/transfer"
    create_id = {
        "list_id": remittance_create_id, 
        "status":"2"
    }
    resultTransfer = await call_api(session, url_transfer, create_id)
    if not resultTransfer or resultTransfer.get("success_code") != 2000:
        logging.error(f"TaskID : {data['task_id']} >>>> 송금 확정 API 실패: "+json.dumps(resultTransfer, ensure_ascii=False))
        logging.debug(f"TaskID : {data['task_id']} >>>> ===이체 실패===")
        return
    
    resultTransfer=None

    # 4. 수금 확정 API
    logging.debug(f"TaskID : {data['task_id']} >>>> ===4. 수금 확정 API 시작===")
    logging.info(f" TaskID : {data['task_id']} >>>> Create ID  : {receive_create_id}")
    url_transfer = "http://"+serverurl+"/"+receivebank+"/transfer"
    create_id = {
        "list_id": receive_create_id, 
        "status":"2"
    }
    resultTransfer = await call_api(session, url_transfer, create_id)
    if not resultTransfer or resultTransfer.get("success_code") != 2000:
        logging.error(f"TaskID : {data['task_id']} >>>> 수금 확정 API 실패: "+json.dumps(resultTransfer, ensure_ascii=False))

        logging.debug(f"TaskID : {data['task_id']} >>>> ===이체 실패===")
        return

    logging.debug(f"TaskID : {data['task_id']} >>>> ===5. 이체 완료===")
    logging.debug(f"==========================================================")

async def generate_data(session, n, interval):
    """
    초당 n개의 데이터를 생성하는 함수
    """
    tasks = []
    count = 0
    while count < n:
        remittance = random.randint(0, dataCount)
        recive = random.randint(0, dataCount)
        while remittance == recive:
            recive = random.randint(0, dataCount)

        data = {
            "sender_id": peoples[remittance],
            "receiver_id": peoples[recive],
            "amount": random.randint(0, 1000) * (10 ** random.randint(1, 4)),
            "task_id": count
        }
        tasks.append(process_chain(session, data))
        count += 1
        if count % n == 0:
            await asyncio.sleep(interval)  # interval 초 간격으로 n개씩 생성

    await asyncio.gather(*tasks)

async def fff(cnt):
    count = 0
    while count < cnt:
        print(count)
        count+=1
    print("=========================================")
