#!/bin/bash
# RDG (Random Data Generator) 실행 스크립트

set -e  # 오류 발생 시 즉시 종료

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
python RDG_v1.py

# 가상환경 비활성화는 자동으로 처리됨
