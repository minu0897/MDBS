#Random Data Generator Python file
import asyncio
import aiohttp
import csv
import random
import logging
import json
import time
import os
import sys
import RDG
import asyncio

from Backend.Data.RDG import RDG_CONFIG
from Backend.common.config.Flaskconfig import FLASK_CONFIG

serverurl = FLASK_CONFIG["SERVERIP"]+":"+FLASK_CONFIG["SERVERPORT"]
peoples=[]
dataCount=RDG_CONFIG["DATA_COUNT"]#현재까지 실제DB에 있는 data의 갯수

stop_event = asyncio.Event()
        
async def main():
    while not stop_event.is_set():
        async with aiohttp.ClientSession() as session:
            await RDG.generate_data(session, RDG_CONFIG["countPerSec"], 1, peoples)  
            time.sleep(1)

async def stop_after(delay):
    stop_event.set()  # 종료 신호 발생

   
if __name__ == "__main__":
    with open("Data/data.csv", mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            peoples.append("00"+str(row[0]))
    asyncio.run(main())
