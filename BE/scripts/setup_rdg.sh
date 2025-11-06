#!/bin/bash
# RDG (Random Data Generator) 설치 스크립트

set -e  # 오류 발생 시 즉시 종료

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "RDG 환경 설정 시작"
echo "=========================================="

# 1. Python3 설치 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3가 설치되어 있지 않습니다."
    echo "다음 명령어로 설치하세요:"
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "✓ Python 버전: $(python3 --version)"

# 2. 가상환경 생성
if [ -d "venv" ]; then
    echo "⚠️  기존 가상환경이 있습니다. 삭제하고 새로 생성하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🗑️  기존 가상환경 삭제 중..."
        rm -rf venv
    else
        echo "기존 가상환경을 사용합니다."
    fi
fi

if [ ! -d "venv" ]; then
    echo "📦 가상환경 생성 중..."
    python3 -m venv venv
fi

# 3. 가상환경 활성화
echo "🔧 가상환경 활성화..."
source venv/bin/activate

# 4. pip 업그레이드
echo "⬆️  pip 업그레이드..."
pip install --upgrade pip

# 5. 패키지 설치
echo "📥 패키지 설치 중..."
if [ -f "requirements_rdg.txt" ]; then
    pip install -r requirements_rdg.txt
else
    echo "⚠️  requirements_rdg.txt가 없습니다. 직접 설치합니다."
    pip install aiohttp==3.9.5 python-dotenv==1.0.1
fi

echo ""
echo "=========================================="
echo "✅ RDG 환경 설정 완료!"
echo "=========================================="
echo ""
echo "다음 명령어로 실행하세요:"
echo "  ./run_rdg.sh"
echo ""
echo "또는 백그라운드 실행:"
echo "  nohup ./run_rdg.sh > rdg.log 2>&1 &"
echo ""

# 가상환경 비활성화
deactivate
