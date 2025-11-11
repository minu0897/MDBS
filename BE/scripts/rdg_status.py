#!/usr/bin/env python3
"""
RDG 통계 조회 스크립트
실행 중인 RDG의 통계를 로그 파일에서 파싱하여 출력합니다.

사용법:
    python rdg_status.py
    python rdg_status.py --json  # JSON 형식으로 출력
    python rdg_status.py --watch  # 실시간 모니터링
"""
import sys
import os
import re
import time
import json
import argparse
from pathlib import Path

# services 모듈을 import하기 위해 부모 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rdg_runner import runner

def format_uptime(seconds):
    """초를 사람이 읽기 쉬운 형태로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def print_stats(status_data, as_json=False):
    """통계 출력"""
    if as_json:
        # JSON 형식으로 출력
        print(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    # 사람이 읽기 쉬운 형식으로 출력
    running = status_data.get("running", False)
    stats = status_data.get("stats", {})
    cfg = status_data.get("cfg", {})
    base_url = status_data.get("base_url")

    print("\n" + "=" * 60)
    print("📊 RDG 상태")
    print("=" * 60)

    # 실행 상태
    status_icon = "🟢" if running else "🔴"
    status_text = "실행 중" if running else "중지됨"
    print(f"{status_icon} 상태: {status_text}")

    if base_url:
        print(f"🌐 서버: {base_url}")

    if cfg:
        print(f"⚙️  설정:")
        print(f"   - RPS: {cfg.get('rps', 'N/A')}")
        print(f"   - Concurrent: {cfg.get('concurrent', 'N/A')}")
        print(f"   - DBMS: {', '.join(cfg.get('active_dbms', [])) if cfg.get('active_dbms') else 'N/A'}")

    print("\n" + "-" * 60)
    print("📈 통계")
    print("-" * 60)

    uptime = stats.get('uptime_sec', 0)
    print(f"⏱️  실행 시간:    {format_uptime(uptime)} ({uptime:.2f}초)")
    print(f"📨 전송:         {stats.get('sent', 0):,}건")
    print(f"✅ 성공:         {stats.get('ok', 0):,}건")
    print(f"❌ 실패:         {stats.get('fail', 0):,}건")

    success_rate = stats.get('success_rate', 0)
    if success_rate == 0 and stats.get('sent', 0) > 0:
        # success_rate가 없으면 계산
        success_rate = (stats.get('ok', 0) / stats.get('sent', 1)) * 100

    print(f"🎯 성공률:       {success_rate:.2f}%")
    print(f"📈 실제 RPS:     {stats.get('actual_rps', 0):.2f}")
    print(f"⏳ 평균 지연:    {stats.get('avg_latency_ms', 0):.2f}ms")
    print(f"🔄 처리 중:      {stats.get('in_flight', 0)}건")

    print("=" * 60 + "\n")

def watch_stats(interval=5, as_json=False):
    """실시간 통계 모니터링"""
    print("🔄 실시간 모니터링 시작 (Ctrl+C로 종료)\n")
    try:
        while True:
            # 화면 클리어 (선택적)
            if not as_json and os.name == 'nt':
                os.system('cls')
            elif not as_json:
                os.system('clear')

            status_data = runner.status()
            print_stats(status_data, as_json)

            if not as_json:
                print(f"⏰ 마지막 업데이트: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   ({interval}초마다 자동 갱신)")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n모니터링 종료")

def main():
    parser = argparse.ArgumentParser(
        description='RDG 통계 조회',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python rdg_status.py              # 현재 통계 출력
  python rdg_status.py --json       # JSON 형식으로 출력
  python rdg_status.py --watch      # 5초마다 자동 갱신
  python rdg_status.py -w -i 2      # 2초마다 자동 갱신
        """
    )
    parser.add_argument('--json', '-j', action='store_true',
                       help='JSON 형식으로 출력')
    parser.add_argument('--watch', '-w', action='store_true',
                       help='실시간 모니터링 모드')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='모니터링 간격(초) (기본: 5)')

    args = parser.parse_args()

    if args.watch:
        watch_stats(args.interval, args.json)
    else:
        status_data = runner.status()
        print_stats(status_data, args.json)

if __name__ == "__main__":
    main()
