# RDG (Random Data Generator) 우분투 서버 실행 가이드

## 사전 준비 파일
- RDG_v1.py
- rdg_config.py  
- requirements_rdg.txt
- setup_rdg.sh
- run_rdg.sh
- BE/.env.server

## 설치 및 실행

### 1. 스크립트 권한 부여
chmod +x setup_rdg.sh run_rdg.sh

### 2. 환경 설정 (최초 1회)
./setup_rdg.sh

### 3. 실행
./run_rdg.sh

### 4. 백그라운드 실행
nohup ./run_rdg.sh > rdg.log 2>&1 &

## 종료
pkill -f RDG_v1.py
