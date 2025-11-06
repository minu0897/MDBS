# BE/scripts/run_rdg.py
"""
RDG 실행 스크립트 (설정 파일 사용)
rdg_config.py의 설정을 사용하여 RDG를 실행합니다.

사용법:
    python run_rdg.py
"""
import asyncio
import logging
from RDG_v1 import RDGConfig, RDGRunner, setup_logger

# 설정 파일 import
try:
    from rdg_config import (
        BASE_URL,
        RPS,
        CONCURRENT_LIMIT,
        ACTIVE_DBMS,
        MIN_AMOUNT,
        MAX_AMOUNT,
        ALLOW_SAME_DB,
        LOG_LEVEL,
        LOG_FILE,
        DURATION,
        STATS_INTERVAL
    )
except ImportError as e:
    print(f"설정 파일을 불러올 수 없습니다: {e}")
    print("rdg_config.py 파일이 같은 디렉토리에 있는지 확인하세요.")
    exit(1)

async def main():
    """메인 함수"""
    # 로그 레벨 변환
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = log_level_map.get(LOG_LEVEL.upper(), logging.DEBUG)

    # 로거 설정
    logger = setup_logger(log_level)

    # 설정 생성
    config = RDGConfig(
        base_url=BASE_URL,
        rps=RPS,
        concurrent_limit=CONCURRENT_LIMIT,
        active_dbms=ACTIVE_DBMS,
        min_amount=MIN_AMOUNT,
        max_amount=MAX_AMOUNT,
        allow_same_db=ALLOW_SAME_DB
    )

    # 설정 검증
    if not config.active_dbms:
        logger.error("활성화된 DBMS가 없습니다. rdg_config.py의 ACTIVE_DBMS를 확인하세요.")
        return

    if len(config.active_dbms) == 1 and not config.allow_same_db:
        logger.error("ACTIVE_DBMS가 1개인데 ALLOW_SAME_DB=False입니다. 거래가 불가능합니다.")
        return

    # 실행
    runner = RDGRunner(config)
    await runner.run(duration=DURATION)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램 종료")
    except Exception as e:
        print(f"오류 발생: {e}")
