# BE/scripts/rdg_config.py
"""
RDG 설정 파일
이 파일을 수정하여 RDG 동작을 커스터마이즈할 수 있습니다.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# 환경 변수 파일 로드
# 기본값: .env.dev (로컬 PC에서 실행)
# 서버에서 실행 시: python run_rdg.py --env server 또는 환경 변수 ENV=server로 설정
env_type = os.getenv("ENV", "dev")
env_file = Path(__file__).parent.parent / f".env.{env_type}"

if env_file.exists():
    load_dotenv(env_file)
    print(f"환경 설정 로드: {env_file}")
else:
    print(f"경고: {env_file} 파일을 찾을 수 없습니다. 기본값을 사용합니다.")

# ==================== 서버 설정 ====================
# 서버 URL 설정 (환경 변수에서 로드)
# .env.dev: http://ip:port (로컬 PC에서 실행)
# .env.server: http://localhost:5000 (서버에서 실행)
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# ==================== 성능 설정 ====================
# 초당 생성할 거래 수 (Requests Per Second)
# 예: RPS=10 → 초당 10개의 거래 생성
#RPS = 5
RPS = 2
# 동시 처리 제한
# 동시에 처리할 수 있는 최대 연결 수
#CONCURRENT_LIMIT = 30
CONCURRENT_LIMIT = 4

# ==================== DBMS 설정 ====================
# 활성화할 DBMS 리스트
# 가능한 값: "mysql", "postgres", "oracle", "mongo"
# 예: ACTIVE_DBMS = ["mysql", "postgres"] → MySQL과 PostgreSQL만 사용
ACTIVE_DBMS: List[str] = [
    "mysql",
    "postgres",
    "oracle"
    #,"mongo"
]

# ==================== 계좌 설정 ====================
# 계좌 번호는 자동으로 생성됩니다.
# 형식: [은행구분 1자리][0-795 랜덤값]
# 은행구분: 1=mongo, 2=mysql, 3=oracle, 4=postgres
# 예: mongo(100000~100795), mysql(200000~200795), oracle(300000~300795), postgres(400000~400795)
# ACCOUNT_RANGE = (200000, 200200)  # 더 이상 사용하지 않음

# ==================== 금액 설정 ====================
# 거래 최소 금액
MIN_AMOUNT = 1_000

# 거래 최대 금액
MAX_AMOUNT = 100_000

# ==================== 이체 설정 ====================
# 같은 DBMS 내 이체 허용 여부
# True: 같은 DBMS 내에서도 이체 가능 (MySQL → MySQL)
# False: 항상 다른 DBMS로만 이체 (MySQL → PostgreSQL)
ALLOW_SAME_DB = True

# ==================== 로그 설정 ====================
# 로그 레벨
# "DEBUG": 모든 상세 로그 출력
# "INFO": 일반 정보 로그 출력
# "WARNING": 경고 및 에러만 출력
LOG_LEVEL = "DEBUG"

# 로그 파일 경로
LOG_FILE = "rdg_v1.log"

# ==================== 실행 설정 ====================
# 실행 시간 (초)
# None: 무한 실행 (Ctrl+C로 종료)
# 숫자: 지정된 시간(초) 동안만 실행
# 예: DURATION = 60 → 60초 동안만 실행
DURATION = None

# 통계 출력 주기 (초)
# 예: STATS_INTERVAL = 10 → 10초마다 통계 출력
STATS_INTERVAL = 10
