#!/bin/bash
# RDG (Random Data Generator) 실행 스크립트
# 사용법:
#   포그라운드: ./run_rdg.sh
#   백그라운드: ./run_rdg.sh -d 또는 ./run_rdg.sh --daemon

set -e  # 오류 발생 시 즉시 종료

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 데몬 모드 확인
DAEMON_MODE=false
if [[ "$1" == "-d" ]] || [[ "$1" == "--daemon" ]]; then
    DAEMON_MODE=true
fi

# 백그라운드 모드로 재실행
if [ "$DAEMON_MODE" = true ] && [ -z "$RDG_DAEMON_RUNNING" ]; then
    export RDG_DAEMON_RUNNING=1
    LOG_FILE="rdg_$(date +%Y%m%d_%H%M%S).log"
    echo "=========================================="
    echo "RDG를 백그라운드로 실행합니다"
    echo "로그 파일: $LOG_FILE"
    echo "=========================================="
    nohup "$0" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "프로세스 ID: $PID"
    echo "로그 확인: tail -f $LOG_FILE"
    echo "종료: kill $PID"
    exit 0
fi

echo "=========================================="
echo "RDG (Random Data Generator) 시작"
echo "=========================================="

# 1. 가상환경 존재 확인
if [ ! -d "venv" ]; then
    echo "❌ 가상환경이 없습니다. setup_rdg.sh를 먼저 실행하세요."
    exit 1
fi

# 2. 가상환경 활성화
echo "🔧 가상환경 활성화..."
source venv/bin/activate

# 3. 환경 변수 설정 (서버에서 실행)
export ENV=server

# 4. RDG 실행
echo "🚀 RDG 실행 중..."
./venv/bin/python RDG_v1.py

# 가상환경 비활성화는 자동으로 처리됨
