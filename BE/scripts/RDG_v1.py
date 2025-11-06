# BE/scripts/RDG_v1.py
"""
Random Data Generator v1
서버에서 실행되어 자동으로 랜덤 거래 데이터를 생성하는 프로그램
"""
import asyncio
import aiohttp
import random
import logging
import time
import uuid
import signal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from decimal import Decimal

# ==================== 설정 ====================
@dataclass
class RDGConfig:
    """RDG 설정"""
    # 서버 설정
    base_url: str = "http://localhost:5000"  # 로컬 실행시 / 서버에서 실행시 localhost로 변경

    # 성능 설정
    rps: int = 10  # 초당 생성할 데이터 수 (Requests Per Second)
    concurrent_limit: int = 50  # 동시 처리 제한

    # DBMS 설정 (활성화할 DBMS만 리스트에 포함)
    # rdg_config.py에서 설정 필수!
    active_dbms: List[str] = None

    # 금액 설정
    min_amount: int = 1_000
    max_amount: int = 100_000

    # 이체 설정
    allow_same_db: bool = True  # 같은 DBMS 내 이체 허용 여부

    def __post_init__(self):
        if self.active_dbms is None or len(self.active_dbms) == 0:
            raise ValueError("active_dbms must be set in rdg_config.py")

# ==================== 로깅 설정 ====================
def setup_logger(log_level: int = logging.INFO) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger("RDG")
    logger.setLevel(log_level)
    logger.propagate = False  # 부모 로거로 전파 방지

    # 기존 핸들러 제거 (중복 방지)
    if logger.hasHandlers():
        logger.handlers.clear()

    # 파일 핸들러
    file_handler = logging.FileHandler('rdg_v1.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)  # 파라미터로 받은 log_level 사용

    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

# ==================== 통계 ====================
class Stats:
    """통계 수집"""
    def __init__(self):
        self.total_sent = 0
        self.total_success = 0
        self.total_fail = 0
        self.start_time = time.time()
        self.last_report = time.time()

    def increment_sent(self):
        self.total_sent += 1

    def increment_success(self):
        self.total_success += 1

    def increment_fail(self):
        self.total_fail += 1

    def report(self):
        """통계 리포트"""
        elapsed = time.time() - self.start_time
        actual_rps = self.total_sent / elapsed if elapsed > 0 else 0
        success_rate = (self.total_success / self.total_sent * 100) if self.total_sent > 0 else 0

        logger.info("=" * 60)
        logger.info(f"경과 시간: {elapsed:.2f}초")
        logger.info(f"전송: {self.total_sent} | 성공: {self.total_success} | 실패: {self.total_fail}")
        logger.info(f"실제 RPS: {actual_rps:.2f} | 성공률: {success_rate:.2f}%")
        logger.info("=" * 60)

stats = Stats()

# DBMS별 은행 구분 코드 (십만 자리)


# ==================== 랜덤 데이터 생성기 ====================
class RandomDataGenerator:
    """랜덤 거래 데이터 생성기"""
    BANK_CODE_MAP = {
        "mongo": 1,
        "mysql": 2,
        "oracle": 3,
        "postgres": 4
    }
    def __init__(self, config: RDGConfig):
        self.config = config
        # account_range는 더 이상 사용하지 않음 (동적 생성)

    def _generate_account_number(self, dbms: str) -> int:
        """
        DBMS에 맞는 6자리 계좌번호 생성
        형식: [은행구분 1자리][0-795 범위를 5자리로 패딩]
        예: mongo(1) + 795 → 100795
        """
        bank_code = self.BANK_CODE_MAP.get(dbms, 1)
        random_num = random.randint(0, 795)
        # 은행구분(1자리) + 랜덤값을 5자리로 제로패딩
        account_number = bank_code * 100000 + random_num
        return account_number

    def generate_transaction(self) -> Dict[str, Any]:
        """랜덤 거래 생성"""
        # DBMS 선택
        src_dbms = random.choice(self.config.active_dbms)
        if self.config.allow_same_db:
            dst_dbms = random.choice(self.config.active_dbms)
        else:
            # 다른 DBMS만 선택
            dst_dbms = random.choice([d for d in self.config.active_dbms if d != src_dbms])

        # 송금/수취 계좌 생성 (각 DBMS에 맞는 은행 코드 사용)
        src_account = self._generate_account_number(src_dbms)
        dst_account = self._generate_account_number(dst_dbms)

        # 같은 계좌 방지 (같은 DBMS인 경우만 체크)
        while src_dbms == dst_dbms and dst_account == src_account:
            dst_account = self._generate_account_number(dst_dbms)

        # 금액 생성
        amount = random.randint(self.config.min_amount, self.config.max_amount)


        # 멱등키 생성
        idempotency_key = src_dbms[0]+dst_dbms[0]+"-"+str(uuid.uuid4())

        # 거래 타입 결정
        if src_dbms == dst_dbms:
            tx_type = "1"  # 내부 이체
        else:
            tx_type = "2"  # 외부 송금 (송금측 기준)

        return {
            "src_account_id": src_account,
            "dst_account_id": dst_account,
            "src_dbms": src_dbms,
            "dst_dbms": dst_dbms,
            "amount": amount,
            "idempotency_key": idempotency_key,
            "type": tx_type
        }

# ==================== API 클라이언트 ====================
class APIClient:
    """백엔드 API 클라이언트"""

    def __init__(self, config: RDGConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')

    async def call_sql_procedure(
        self,
        session: aiohttp.ClientSession,
        dbms: str,
        proc_name: str,
        args: List[Any],
        out_count: int = 0,
        out_names: List[str] = None,
        mode: str = "proc"
    ) -> Optional[Dict]:
        """SQL 프로시저 호출 (MySQL, PostgreSQL, Oracle)"""
        url = f"{self.base_url}/db/proc/exec"

        payload = {
            "dbms": dbms,
            "name": proc_name,
            "args": args,
            "mode": mode
        }

        if out_count > 0:
            payload["out_count"] = out_count

        if out_names:
            payload["out_names"] = out_names

        # Oracle 전용: OUT 자리에 placeholder 추가
        if dbms == "oracle" and out_count > 0:
            # 프로시저별 OUT 타입 매핑
            if proc_name == "sp_remittance_hold":
                payload["out_types"] = ["NUMBER", "VARCHAR2"]  # txn_id, status
            elif proc_name == "sp_remittance_release":
                payload["out_types"] = ["VARCHAR2", "VARCHAR2"]  # status, result
            elif proc_name == "sp_receive_prepare":
                payload["out_types"] = ["NUMBER", "VARCHAR2"]  # txn_id, status
            elif proc_name == "sp_confirm_debit_local":
                payload["out_types"] = ["NUMBER", "VARCHAR2", "VARCHAR2"]  # txn_id, status, result
            elif proc_name == "sp_confirm_credit_local":
                payload["out_types"] = ["NUMBER", "VARCHAR2", "VARCHAR2"]  # txn_id, status, result
            elif proc_name == "sp_transfer_confirm_internal":
                payload["out_types"] = ["VARCHAR2", "VARCHAR2"]  # status, result
            else:
                # 기본값 (기존 로직)
                payload["out_types"] = ["NUMBER", "VARCHAR2"] * (out_count // 2 + 1)

            # OUT 자리에 None 추가 (Oracle adapter가 이 자리를 OUT 변수로 바인딩)
            payload["args"] = args + [None] * out_count

        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                result = await resp.json()
                if resp.status >= 200 and resp.status < 300:
                    return result.get("data")
                else:
                    logger.error(f"API 에러 [{dbms}/{proc_name}]: {result}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"타임아웃 [{dbms}/{proc_name}]")
            return None
        except Exception as e:
            logger.error(f"예외 발생 [{dbms}/{proc_name}]: {e}")
            return None

    async def call_mongo_procedure(
        self,
        session: aiohttp.ClientSession,
        operation: str,
        payload: Dict
    ) -> Optional[Dict]:
        """MongoDB 프로시저 호출"""
        url = f"{self.base_url}/mongo_proc/{operation}"

        try:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                result = await resp.json()
                if resp.status >= 200 and resp.status < 300:
                    return result.get("data")
                else:
                    logger.error(f"API 에러 [mongo/{operation}]: {result}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"타임아웃 [mongo/{operation}]")
            return None
        except Exception as e:
            logger.error(f"예외 발생 [mongo/{operation}]: {e}")
            return None

# ==================== 거래 처리기 ====================
class TransactionProcessor:
    """거래 처리기"""

    def __init__(self, config: RDGConfig):
        self.config = config
        self.api_client = APIClient(config)

    async def process_transaction(self, session: aiohttp.ClientSession, tx_data: Dict) -> bool:
        """거래 처리"""
        src_dbms = tx_data["src_dbms"]
        dst_dbms = tx_data["dst_dbms"]
        src_account = tx_data["src_account_id"]
        dst_account = tx_data["dst_account_id"]
        amount = tx_data["amount"]
        idem_key = tx_data["idempotency_key"]
        tx_type = tx_data["type"]

        logger.debug(f"거래 시작 [{idem_key}]: {src_dbms}({src_account}) → {dst_dbms}({dst_account}), {amount}원")

        try:
            if src_dbms == dst_dbms:
                # 같은 DBMS: 내부 이체
                return await self._process_internal_transfer(session, src_dbms, tx_data)
            else:
                # 다른 DBMS: 외부 이체
                return await self._process_external_transfer(session, tx_data)
        except Exception as e:
            logger.error(f"거래 처리 실패 [{idem_key}]: {e}")
            return False

    async def _process_internal_transfer(
        self,
        session: aiohttp.ClientSession,
        dbms: str,
        tx_data: Dict
    ) -> bool:
        """내부 이체 처리 (같은 DBMS)"""
        src_account = tx_data["src_account_id"]
        dst_account = tx_data["dst_account_id"]
        dst_bank = str(dst_account // 100000) # 받는 쪽 은행코드 (문자열로 변환)
        amount = tx_data["amount"]
        idem_key = tx_data["idempotency_key"]

        # Step 1: 송금 보류
        logger.debug(f"  [{idem_key}] Step 1: 송금 보류 ({dbms})")

        if dbms == "mongo":
            result = await self.api_client.call_mongo_procedure(
                session,
                "remittance/hold",
                {
                    "src_account_id": src_account,
                    "dst_account_id": dst_account,
                    "dst_bank": dst_bank,  # 내부
                    "amount": str(amount),
                    "idempotency_key": idem_key,
                    "type": "1"
                }
            )
        else:
            result = await self.api_client.call_sql_procedure(
                session,
                dbms,
                "sp_remittance_hold",
                [src_account, dst_account, dst_bank, amount, idem_key, "1"],
                out_count=2,
                out_names=["txn_id", "status"],
                mode="func" if dbms == "postgres" else "proc"
            )

        if not result or result.get("status") != "1":
            logger.warning(f"  [{idem_key}] 송금 보류 실패: {result}")
            return False

        # Step 2: 이체 확정
        logger.debug(f"  [{idem_key}] Step 2: 이체 확정 ({dbms})")

        if dbms == "mongo":
            result = await self.api_client.call_mongo_procedure(
                session,
                "transfer/confirm/internal",
                {"idempotency_key": idem_key}
            )
        else:
            result = await self.api_client.call_sql_procedure(
                session,
                dbms,
                "sp_transfer_confirm_internal",
                [idem_key],
                out_count=2,
                out_names=["status", "result"],
                mode="func" if dbms == "postgres" else "proc"
            )

        if not result or result.get("status") != "2":
            logger.warning(f"  [{idem_key}] 이체 확정 실패: {result}")
            # 실패 시 hold 해제
            await self._release_hold(session, dbms, idem_key)
            return False

        logger.info(f"✓ 내부 이체 완료 [{idem_key}]: {dbms}({src_account} → {dst_account}), {amount}원")
        return True

    async def _process_external_transfer(
        self,
        session: aiohttp.ClientSession,
        tx_data: Dict
    ) -> bool:
        """외부 이체 처리 (다른 DBMS)"""
        src_dbms = tx_data["src_dbms"]
        dst_dbms = tx_data["dst_dbms"]
        src_account = tx_data["src_account_id"]
        dst_account = tx_data["dst_account_id"]
        amount = tx_data["amount"]
        idem_key = tx_data["idempotency_key"]

        # 송금측 멱등키 (송금)
        idem_key_debit = f"{idem_key}_debit"
        # 수취측 멱등키 (수금)
        idem_key_credit = f"{idem_key}_credit"

        # 도착 은행 코드 (수취 계좌의 은행 코드)
        dst_bank = str(dst_account // 100000)

        # Step 1: 송금 보류 (송금측 DBMS)
        logger.debug(f"  [{idem_key}] Step 1: 송금 보류 ({src_dbms})")

        if src_dbms == "mongo":
            result = await self.api_client.call_mongo_procedure(
                session,
                "remittance/hold",
                {
                    "src_account_id": src_account,
                    "dst_account_id": dst_account,
                    "dst_bank": dst_bank,
                    "amount": str(amount),
                    "idempotency_key": idem_key_debit,
                    "type": "2"
                }
            )
        else:
            result = await self.api_client.call_sql_procedure(
                session,
                src_dbms,
                "sp_remittance_hold",
                [src_account, dst_account, dst_bank, amount, idem_key_debit, "2"],
                out_count=2,
                out_names=["txn_id", "status"],
                mode="func" if src_dbms == "postgres" else "proc"
            )

        if not result or result.get("status") != "1":
            logger.warning(f"  [{idem_key}] 송금 보류 실패: {result}")
            return False

        # Step 2: 수금 준비 (수취측 DBMS)
        logger.debug(f"  [{idem_key}] Step 2: 수금 준비 ({dst_dbms})")

        if dst_dbms == "mongo":
            result = await self.api_client.call_mongo_procedure(
                session,
                "receive/prepare",
                {
                    "src_account_id": src_account,
                    "dst_account_id": dst_account,
                    "dst_bank": dst_bank,
                    "amount": str(amount),
                    "idempotency_key": idem_key_credit,
                    "type": "3"
                }
            )
        else:
            result = await self.api_client.call_sql_procedure(
                session,
                dst_dbms,
                "sp_receive_prepare",
                [src_account, dst_account, dst_bank, amount, idem_key_credit, "3"],
                out_count=2,
                out_names=["txn_id", "status"],
                mode="func" if dst_dbms == "postgres" else "proc"
            )

        if not result or result.get("status") != "1":
            logger.warning(f"  [{idem_key}] 수금 준비 실패: {result}")
            # 실패 시 송금측 hold 해제
            await self._release_hold(session, src_dbms, idem_key_debit)
            return False

        # Step 3: 출금 확정 (송금측 DBMS)
        logger.debug(f"  [{idem_key}] Step 3: 출금 확정 ({src_dbms})")

        if src_dbms == "mongo":
            result = await self.api_client.call_mongo_procedure(
                session,
                "confirm/debit/local",
                {"idempotency_key": idem_key_debit}
            )
        else:
            result = await self.api_client.call_sql_procedure(
                session,
                src_dbms,
                "sp_confirm_debit_local",
                [idem_key_debit],
                out_count=3,
                out_names=["txn_id", "status", "result"],
                mode="func" if src_dbms == "postgres" else "proc"
            )

        if not result or result.get("status") != "2":
            logger.warning(f"  [{idem_key}] 출금 확정 실패: {result}")
            # 출금 확정 실패 시 hold 해제
            await self._release_hold(session, src_dbms, idem_key_debit)
            return False

        # Step 4: 입금 확정 (수취측 DBMS)
        logger.debug(f"  [{idem_key}] Step 4: 입금 확정 ({dst_dbms})")

        if dst_dbms == "mongo":
            result = await self.api_client.call_mongo_procedure(
                session,
                "confirm/credit/local",
                {"idempotency_key": idem_key_credit}
            )
        else:
            result = await self.api_client.call_sql_procedure(
                session,
                dst_dbms,
                "sp_confirm_credit_local",
                [idem_key_credit],
                out_count=3,
                out_names=["txn_id", "status", "result"],
                mode="func" if dst_dbms == "postgres" else "proc"
            )

        if not result or result.get("status") != "2":
            logger.warning(f"  [{idem_key}] 입금 확정 실패: {result}")
            return False

        logger.info(f"✓ 외부 이체 완료 [{idem_key}]: {src_dbms}({src_account}) → {dst_dbms}({dst_account}), {amount}원")
        return True

    async def _release_hold(
        self,
        session: aiohttp.ClientSession,
        dbms: str,
        idempotency_key: str
    ):
        """Hold 해제 (거래 실패 시 호출)"""
        logger.debug(f"  [{idempotency_key}] Hold 해제 시도 ({dbms})")

        try:
            if dbms == "mongo":
                result = await self.api_client.call_mongo_procedure(
                    session,
                    "remittance/release",
                    {"idempotency_key": idempotency_key}
                )
            else:
                result = await self.api_client.call_sql_procedure(
                    session,
                    dbms,
                    "sp_remittance_release",
                    [idempotency_key],
                    out_count=2,
                    out_names=["status", "result"],
                    mode="func" if dbms == "postgres" else "proc"
                )

            if result and result.get("status") == "3":
                logger.info(f"  [{idempotency_key}] Hold 해제 완료 ({dbms})")
            elif result and result.get("result") in ["ALREADY_RELEASED", "ALREADY_CAPTURED"]:
                logger.debug(f"  [{idempotency_key}] Hold 이미 처리됨: {result.get('result')}")
            else:
                logger.warning(f"  [{idempotency_key}] Hold 해제 실패: {result}")
        except Exception as e:
            logger.error(f"  [{idempotency_key}] Hold 해제 중 예외 발생: {e}")

# ==================== 메인 러너 ====================
class RDGRunner:
    """RDG 메인 러너"""

    def __init__(self, config: RDGConfig):
        self.config = config
        self.data_generator = RandomDataGenerator(config)
        self.tx_processor = TransactionProcessor(config)
        self.running = False
        self.shutdown_requested = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """시그널 핸들러 설정 (백그라운드 실행 대비)"""
        try:
            # SIGTERM: kill 명령어 (기본)
            signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
            # SIGINT: Ctrl+C
            signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        except Exception as e:
            # Windows에서는 일부 시그널이 지원되지 않을 수 있음
            logger.debug(f"시그널 핸들러 설정 중 경고: {e}")

    def _handle_shutdown_signal(self, signum, frame):
        """종료 시그널 처리"""
        sig_name = signal.Signals(signum).name
        logger.info(f"종료 시그널 수신: {sig_name}")
        self.shutdown_requested = True
        self.running = False

    async def run(self, duration: Optional[int] = None):
        """
        RDG 실행

        Args:
            duration: 실행 시간(초). None이면 무한 실행
        """
        self.running = True
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("Random Data Generator v1 시작")
        logger.info(f"서버: {self.config.base_url}")
        logger.info(f"목표 RPS: {self.config.rps}")
        logger.info(f"활성 DBMS: {', '.join(self.config.active_dbms)}")
        logger.info(f"동시 처리 제한: {self.config.concurrent_limit}")
        logger.info("=" * 60)

        connector = aiohttp.TCPConnector(limit=self.config.concurrent_limit)
        async with aiohttp.ClientSession(connector=connector) as session:
            pending_tasks = []
            try:
                tick_count = 0
                while self.running:
                    tick_start = time.time()

                    # 1초당 rps개의 거래 생성 및 처리
                    tasks = []
                    for _ in range(self.config.rps):
                        tx_data = self.data_generator.generate_transaction()
                        task = asyncio.create_task(self._process_single_transaction(session, tx_data))
                        tasks.append(task)
                        pending_tasks.append(task)

                    # 모든 거래 처리 대기
                    await asyncio.gather(*tasks, return_exceptions=True)

                    # 완료된 task 제거
                    pending_tasks = [t for t in pending_tasks if not t.done()]

                    # 1초 주기 유지
                    elapsed = time.time() - tick_start
                    sleep_time = max(0, 1.0 - elapsed)
                    await asyncio.sleep(sleep_time)

                    tick_count += 1

                    # 10초마다 통계 출력
                    if tick_count % 10 == 0:
                        stats.report()

                    # 실행 시간 체크
                    if duration and (time.time() - start_time) >= duration:
                        logger.info(f"설정된 실행 시간({duration}초) 종료")
                        break

            except KeyboardInterrupt:
                logger.info("사용자에 의해 중단 요청됨 (Ctrl+C)...")
                await self._graceful_shutdown(pending_tasks)

            except Exception as e:
                logger.error(f"예상치 못한 오류 발생: {e}")
                await self._graceful_shutdown(pending_tasks)

            finally:
                # 시그널로 인한 종료도 처리
                if self.shutdown_requested and pending_tasks:
                    await self._graceful_shutdown(pending_tasks)

                self.running = False
                stats.report()
                logger.info("Random Data Generator v1 종료")

    async def _graceful_shutdown(self, pending_tasks: List):
        """진행 중인 작업을 안전하게 종료"""
        logger.info(f"진행 중인 거래 {len(pending_tasks)}개를 완료하는 중...")
        self.running = False

        # 진행 중인 모든 작업이 완료될 때까지 대기 (최대 30초)
        if pending_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*pending_tasks, return_exceptions=True),
                    timeout=30.0
                )
                logger.info("모든 진행 중인 거래가 안전하게 완료되었습니다.")
            except asyncio.TimeoutError:
                logger.warning("일부 거래가 30초 내에 완료되지 않아 강제 종료합니다.")

    async def _process_single_transaction(self, session: aiohttp.ClientSession, tx_data: Dict):
        """단일 거래 처리"""
        stats.increment_sent()

        try:
            success = await self.tx_processor.process_transaction(session, tx_data)
            if success:
                stats.increment_success()
            else:
                stats.increment_fail()
        except Exception as e:
            logger.error(f"거래 처리 중 예외: {e}")
            stats.increment_fail()

# ==================== 실행 ====================
async def main():
    """
    메인 함수 (직접 실행용)

    주의: 이 파일을 직접 실행하는 경우에만 사용됩니다.
    권장: run_rdg.py를 사용하여 설정 파일(rdg_config.py)로 실행하세요.
    """
    try:
        # 설정 파일 import 시도
        from rdg_config import (
            BASE_URL, RPS, CONCURRENT_LIMIT, ACTIVE_DBMS,
            MIN_AMOUNT, MAX_AMOUNT, ALLOW_SAME_DB
        )
        logger.info("rdg_config.py에서 설정을 불러왔습니다.")

        config = RDGConfig(
            base_url=BASE_URL,
            rps=RPS,
            concurrent_limit=CONCURRENT_LIMIT,
            active_dbms=ACTIVE_DBMS,
            min_amount=MIN_AMOUNT,
            max_amount=MAX_AMOUNT,
            allow_same_db=ALLOW_SAME_DB
        )
    except ImportError:
        # 설정 파일이 없는 경우 기본값 사용
        logger.warning("rdg_config.py를 찾을 수 없습니다. 기본 설정을 사용합니다.")
        logger.warning("권장: rdg_config.py 파일을 생성하여 설정을 관리하세요.")

        config = RDGConfig(
            base_url="http://localhost:5000",
            rps=5,
            concurrent_limit=50,
            active_dbms=["mysql", "postgres", "oracle", "mongo"],
            min_amount=1_000,
            max_amount=100_000,
            allow_same_db=True
        )

    # 실행
    runner = RDGRunner(config)
    await runner.run(duration=None)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("프로그램 종료")
