#Random Data Generator Python file
import asyncio
import aiohttp
import csv
import random
import logging
import json
import time
#import RDG
import RDG



import sys
from .config.RDGconfig import RDG_CONFIG
from common.config.Flaskconfig import FLASK_CONFIG
serverurl = FLASK_CONFIG["SERVERIP"]+":"+FLASK_CONFIG["SERVERPORT"]




peoples=[]
dataCount=RDG_CONFIG["DATA_COUNT"]#현재까지 실제DB에 있는 data의 갯수

        
async def main():
    while True:
        async with aiohttp.ClientSession() as session:
            # 초당 100개의 데이터를 생성하도록 설정
            await RDG.generate_data(session, 5, 1,peoples)  
            #await RDG.fff(20)
            time.sleep(1)
            

   
if __name__ == "__main__":
    with open("Data/data.csv", mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            peoples.append("00"+str(row[0]))
    asyncio.run(main())
