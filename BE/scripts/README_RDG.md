# Random Data Generator v1 (RDG)

서버에서 실행되어 자동으로 랜덤 거래 데이터를 생성하는 프로그램입니다.

## 파일 구조

```
BE/scripts/
├── RDG_v1.py          # RDG 메인 코드
├── rdg_config.py      # 설정 파일
├── run_rdg.py         # 실행 스크립트
└── README_RDG.md      # 이 문서
```

## 주요 기능

### 1. 초당 요청 수 조절
- `RPS` 설정으로 초당 생성할 거래 수를 조절할 수 있습니다.
- 예: `RPS=10` → 초당 10개의 거래 생성

### 2. 활성 DBMS 선택
- `ACTIVE_DBMS` 리스트로 사용할 DBMS를 선택할 수 있습니다.
- 예: `["mysql", "postgres"]` → MySQL과 PostgreSQL만 사용

### 3. 자동 거래 처리
- 같은 DBMS 내 이체: 2단계 프로세스
  1. 송금 보류 (`sp_remittance_hold`)
  2. 이체 확정 (`sp_transfer_confirm_internal`)

- 다른 DBMS 간 이체: 4단계 프로세스
  1. 송금 보류 (`sp_remittance_hold`)
  2. 수금 준비 (`sp_receive_prepare`)
  3. 출금 확정 (`sp_confirm_debit_local`)
  4. 입금 확정 (`sp_confirm_credit_local`)

### 4. 비동기 처리
- `asyncio` 및 `aiohttp`를 사용한 고성능 비동기 처리
- 동시 처리 제한으로 서버 부하 조절

### 5. 상세한 로깅
- 거래별 로그 기록
- 주기적인 통계 출력 (전송/성공/실패, RPS, 성공률 등)

## 필수 요구사항

### Python 패키지 설치

```bash
pip install python-dotenv aiohttp
```

## 사용 방법

### 1. 환경 설정

프로그램은 `.env.dev` 또는 `.env.server` 파일에서 BASE_URL을 자동으로 로드합니다.

#### 로컬 PC에서 실행 (기본값)

```bash
# .env.dev 파일 사용 (기본값)
cd BE/scripts
python run_rdg.py
```

이 경우 `BE/.env.dev` 파일의 `BASE_URL=http://ip:port`가 사용됩니다.

#### 서버에서 실행

```bash
# .env.server 파일 사용
cd BE/scripts
ENV=server python run_rdg.py
```

이 경우 `BE/.env.server` 파일의 `BASE_URL=http://localhost:5000`가 사용됩니다.

### 2. 설정 파일 수정

`rdg_config.py` 파일을 열어 성능 및 거래 관련 설정을 수정합니다.

```python
# 초당 거래 생성 수
RPS = 10

# 활성화할 DBMS
ACTIVE_DBMS = ["mysql", "postgres", "oracle", "mongo"]

# 계좌 번호 범위
ACCOUNT_RANGE = (200000, 200200)

# 거래 금액 범위
MIN_AMOUNT = 1_000
MAX_AMOUNT = 100_000

# 같은 DBMS 내 이체 허용 여부
ALLOW_SAME_DB = True
```

**주의:** BASE_URL은 더 이상 `rdg_config.py`에서 수정하지 않습니다. `.env.dev` 또는 `.env.server` 파일에서 수정하세요.

### 3. 실행 방법

#### 방법 1: 설정 파일 사용 (권장)

```bash
# 로컬 PC에서 실행 (.env.dev 사용)
cd BE/scripts
python run_rdg.py

# 서버에서 실행 (.env.server 사용)
cd BE/scripts
ENV=server python run_rdg.py
```

#### 방법 2: 직접 실행

```bash
cd BE/scripts
python RDG_v1.py
```

직접 실행하는 경우도 환경 변수 파일을 자동으로 로드합니다.

### 4. 백그라운드 실행 (서버)

서버에서 백그라운드로 실행하려면:

```bash
# nohup으로 백그라운드 실행
cd BE/scripts
nohup python run_rdg.py > rdg_output.log 2>&1 &

# 또는 screen 사용
screen -S rdg
python run_rdg.py
# Ctrl+A, D로 detach

# 또는 systemd 서비스로 등록 (권장)
sudo systemctl start rdg
sudo systemctl enable rdg  # 부팅 시 자동 시작
```

**백그라운드 프로세스 종료:**

```bash
# PID 확인
ps aux | grep run_rdg

# 안전하게 종료 (진행 중인 거래 완료 후 종료)
kill -SIGTERM <PID>

# 또는
pkill -SIGTERM -f run_rdg.py
```

**주의:**
- `kill -9` (SIGKILL)은 사용하지 마세요! 진행 중인 거래가 불완전하게 종료됩니다.
- `kill` (SIGTERM)을 사용하면 진행 중인 거래를 안전하게 완료한 후 종료됩니다.
- 최대 30초간 진행 중인 거래 완료를 대기합니다.

### 5. 종료

#### 포그라운드 실행 시
- `Ctrl+C`를 눌러 프로그램을 종료합니다.

#### 백그라운드 실행 시
- `kill -SIGTERM <PID>` 명령어로 안전하게 종료합니다.

**안전한 종료 프로세스:**
1. 종료 시그널 수신 (SIGTERM 또는 Ctrl+C)
2. 새로운 거래 생성 중단
3. 진행 중인 거래 완료 대기 (최대 30초)
4. 최종 통계 출력
5. 프로그램 종료

## 설정 상세

### 서버 설정 (환경 변수)

BASE_URL은 `BE/.env.dev` 또는 `BE/.env.server` 파일에서 관리됩니다.

| 환경 | 파일 | BASE_URL 예시 | 사용 시점 |
|------|------|---------------|-----------|
| 개발 | `.env.dev` | `http://ip:port` | 로컬 PC에서 서버로 접속 시 |
| 운영 | `.env.server` | `http://localhost:5000` | 서버 내부에서 실행 시 |

**환경 전환 방법:**
```bash
# 기본값 (개발 환경)
python run_rdg.py

# 운영 환경
ENV=server python run_rdg.py
```

### 성능 설정

| 항목 | 설명 | 기본값 |
|------|------|--------|
| RPS | 초당 거래 생성 수 | 10 |
| CONCURRENT_LIMIT | 동시 처리 제한 | 50 |

### DBMS 설정

| 항목 | 설명 | 가능한 값 |
|------|------|-----------|
| ACTIVE_DBMS | 활성화할 DBMS 리스트 | `["mysql", "postgres", "oracle", "mongo"]` |

**예시:**
- MySQL만 사용: `ACTIVE_DBMS = ["mysql"]`
- MySQL과 PostgreSQL만: `ACTIVE_DBMS = ["mysql", "postgres"]`

### 계좌/금액 설정

| 항목 | 설명 | 기본값 |
|------|------|--------|
| ACCOUNT_RANGE | 계좌 번호 범위 (시작, 끝) | `(200000, 200200)` |
| MIN_AMOUNT | 최소 거래 금액 | 1,000 |
| MAX_AMOUNT | 최대 거래 금액 | 100,000 |

### 이체 설정

| 항목 | 설명 | 기본값 |
|------|------|--------|
| ALLOW_SAME_DB | 같은 DBMS 내 이체 허용 | True |

**주의:**
- `ALLOW_SAME_DB=False`이고 `ACTIVE_DBMS`가 1개인 경우 거래가 불가능합니다.

### 로그 설정

| 항목 | 설명 | 기본값 |
|------|------|--------|
| LOG_LEVEL | 로그 레벨 | "INFO" |
| LOG_FILE | 로그 파일 경로 | "rdg_v1.log" |

**로그 레벨:**
- `DEBUG`: 모든 상세 로그 (거래별 단계 표시)
- `INFO`: 일반 정보 로그 (거래 완료 시만 표시)
- `WARNING`: 경고 및 에러만 표시

### 실행 설정

| 항목 | 설명 | 기본값 |
|------|------|--------|
| DURATION | 실행 시간 (초) | None (무한) |
| STATS_INTERVAL | 통계 출력 주기 (초) | 10 |

## 거래 프로세스

### 내부 이체 (같은 DBMS)

```
1. 송금 보류 (sp_remittance_hold)
   ↓
2. 이체 확정 (sp_transfer_confirm_internal)
   ✓ 완료
```

### 외부 이체 (다른 DBMS)

```
1. 송금 보류 (sp_remittance_hold) - 송금측 DBMS
   ↓
2. 수금 준비 (sp_receive_prepare) - 수취측 DBMS
   ↓
3. 출금 확정 (sp_confirm_debit_local) - 송금측 DBMS
   ↓
4. 입금 확정 (sp_confirm_credit_local) - 수취측 DBMS
   ✓ 완료
```

## 엔드포인트

### SQL DBMS (MySQL, PostgreSQL, Oracle)
- **URL**: `POST /db/proc/exec`
- **Request Body**:
  ```json
  {
    "dbms": "mysql",
    "name": "sp_remittance_hold",
    "args": [200000, 200001, "00", 10000, "uuid-key", "1"],
    "out_count": 2,
    "out_names": ["txn_id", "status"],
    "mode": "proc"
  }
  ```

### MongoDB
- **URL**: `POST /mongo_proc/{operation}`
  - `/mongo_proc/remittance/hold`
  - `/mongo_proc/receive/prepare`
  - `/mongo_proc/confirm/debit/local`
  - `/mongo_proc/confirm/credit/local`
  - `/mongo_proc/transfer/confirm/internal`

- **Request Body**:
  ```json
  {
    "src_account_id": 200000,
    "dst_account_id": 200001,
    "dst_bank": "00",
    "amount": "10000",
    "idempotency_key": "uuid-key",
    "type": "1"
  }
  ```

## 통계 출력 예시

```
============================================================
경과 시간: 30.45초
전송: 300 | 성공: 285 | 실패: 15
실제 RPS: 9.85 | 성공률: 95.00%
============================================================
```

## 트러블슈팅

### 문제: 거래가 실패함

**원인:**
1. 서버가 실행 중이지 않음
2. 계좌 번호가 DB에 존재하지 않음
3. 잔액 부족

**해결:**
1. 백엔드 서버가 실행 중인지 확인
2. 계좌 데이터가 DB에 존재하는지 확인
3. 로그 파일(`rdg_v1.log`)을 확인하여 상세 에러 확인

### 문제: RPS가 설정값보다 낮음

**원인:**
1. 서버 응답이 느림
2. 동시 처리 제한이 너무 낮음

**해결:**
1. 서버 성능 확인
2. `CONCURRENT_LIMIT` 값을 높임
3. `RPS` 값을 낮춤

### 문제: "ACTIVE_DBMS가 1개인데 ALLOW_SAME_DB=False"

**원인:**
- 활성 DBMS가 1개인데 같은 DBMS 내 이체를 허용하지 않음

**해결:**
1. `ALLOW_SAME_DB = True`로 설정, 또는
2. `ACTIVE_DBMS`에 2개 이상의 DBMS 추가

## 참고사항

### 멱등키 (Idempotency Key)

- 모든 거래에 고유한 UUID가 멱등키로 사용됩니다.
- 외부 이체의 경우:
  - 송금측: `{uuid}_debit`
  - 수취측: `{uuid}_credit`

### 거래 타입

- `type="1"`: 내부 이체 (같은 DBMS)
- `type="2"`: 외부 송금 (송금측)
- `type="3"`: 외부 수취 (수취측)

### 거래 상태

- `status="1"`: 생성 완료 / 보류 중
- `status="2"`: 원장 기장 완료 / 확정 완료
- `status="5"`: 잔액 부족
- `status="6"`: 상대 계좌 없음

## 개발자 정보

- **파일 위치**: `BE/scripts/`
- **언어**: Python 3.8+
- **주요 라이브러리**: `asyncio`, `aiohttp`

## 라이선스

이 프로그램은 MDBS 프로젝트의 일부입니다.
