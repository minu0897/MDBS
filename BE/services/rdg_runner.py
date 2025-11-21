# rdg_runner.py
"""
RDG Runner - Subprocess 기반
BE/scripts/run_rdg.py를 subprocess로 실행하고 제어합니다.
"""
import subprocess
import time
import re
import os
import signal
import psutil
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class RDGConfig:
    """RDG 설정"""
    base_url: str = "http://127.0.0.1:5000"
    rps: int = 10
    concurrent: int = 50
    active_dbms: list = None
    min_amount: int = 1_000
    max_amount: int = 100_000
    allow_same_db: bool = True
    log_level: str = "DEBUG"

    def __post_init__(self):
        if self.active_dbms is None:
            self.active_dbms = ["mysql", "postgres", "oracle"]

class RDGRunner:
    """RDG 프로세스 관리자"""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._start_time: Optional[float] = None
        self._cfg: Optional[RDGConfig] = None

        # 스크립트 경로 (BE/scripts/run_rdg.py)
        self.scripts_dir = Path(__file__).parent.parent / "scripts"
        self.run_script = self.scripts_dir / "run_rdg.py"

    def _get_latest_log_file(self) -> Path:
        """최신 RDG 로그 파일 찾기 (rdg_v1_*.log 중 가장 최근 것)"""
        import glob
        log_pattern = str(self.scripts_dir / "rdg_v1_*.log")
        log_files = glob.glob(log_pattern)

        if not log_files:
            # 로그 파일이 없으면 기본 경로 반환
            return self.scripts_dir / "rdg_v1.log"

        # 수정 시간 기준 최신 파일 반환
        latest_log = max(log_files, key=lambda f: Path(f).stat().st_mtime)
        return Path(latest_log)

    def start(self, cfg: RDGConfig):
        """RDG 프로세스 시작"""
        if self.is_running():
            raise RuntimeError("RDG is already running")

        self._cfg = cfg
        self._start_time = time.time()

        # 설정값을 환경 변수로 전달
        env = os.environ.copy()
        env["BASE_URL"] = cfg.base_url
        env["RPS"] = str(cfg.rps)
        env["CONCURRENT_LIMIT"] = str(cfg.concurrent)
        env["MIN_AMOUNT"] = str(cfg.min_amount)
        env["MAX_AMOUNT"] = str(cfg.max_amount)
        env["ALLOW_SAME_DB"] = str(cfg.allow_same_db)
        env["LOG_LEVEL"] = cfg.log_level
        if cfg.active_dbms:
            env["ACTIVE_DBMS"] = ",".join(cfg.active_dbms)
        env["ENV"] = "dev"  # 또는 "server"

        # subprocess로 run_rdg.py 실행
        try:
            # stdout/stderr를 DEVNULL로 설정하여 버퍼 문제 방지
            # 로그는 rdg_v1.log 파일에 기록됨
            self._process = subprocess.Popen(
                ["python", str(self.run_script)],
                cwd=str(self.scripts_dir),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            # 프로세스가 시작될 때까지 잠시 대기
            time.sleep(1)

            # 프로세스가 제대로 시작되었는지 확인
            if self._process.poll() is not None:
                log_file = self._get_latest_log_file()
                raise RuntimeError(f"RDG process failed to start. Check log file: {log_file}")

        except Exception as e:
            self._process = None
            self._start_time = None
            raise RuntimeError(f"Failed to start RDG: {e}")

    def stop(self):
        """RDG 프로세스 중지"""
        stopped = False

        # 1. subprocess로 시작한 프로세스 종료
        if self.is_running():
            try:
                # 프로세스 트리 전체 종료 (자식 프로세스 포함)
                if self._process:
                    parent = psutil.Process(self._process.pid)
                    children = parent.children(recursive=True)

                    # 자식 프로세스 먼저 종료
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass

                    # 부모 프로세스 종료
                    parent.terminate()

                    # 5초 대기 후 강제 종료
                    try:
                        parent.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        parent.kill()
                        for child in children:
                            try:
                                child.kill()
                            except psutil.NoSuchProcess:
                                pass
                    stopped = True

            except Exception as e:
                # fallback: 기본 terminate
                if self._process:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self._process.kill()

            finally:
                self._process = None
                self._start_time = None

        # 2. 외부에서 실행된 run_rdg.py 프로세스 종료
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'run_rdg.py' in ' '.join(cmdline):
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        stopped = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            pass

        return stopped

    def status(self) -> Dict:
        """RDG 상태 및 통계 조회"""
        # subprocess로 시작한 프로세스 체크
        process_running = self.is_running()

        # 외부에서 실행된 run_rdg.py 프로세스 체크
        external_running = self._check_external_process()

        # 로그 파일에서 통계 파싱 (running 여부와 관계없이 시도)
        stats = self._parse_log_stats()

        # 로그 파일 기반 running 판단 제거 (오작동 방지)
        # 프로세스 존재 여부만으로 판단
        running = process_running or external_running
        cfg = self._cfg.__dict__ if self._cfg else None

        # 디버깅 로그
        log_file = self._get_latest_log_file()
        print(f"[DEBUG] Running status check:")
        print(f"  - process_running: {process_running}")
        print(f"  - external_running: {external_running}")
        print(f"  - log_file path: {log_file}")
        print(f"  - log_file exists: {log_file.exists()}")
        print(f"  - FINAL running: {running}")

        return {
            "running": running,
            "cfg": cfg,
            "stats": stats,
            "base_url": self._cfg.base_url if self._cfg else None
        }

    def _check_external_process(self) -> bool:
        """외부에서 실행된 run_rdg.py 또는 RDG_v1.py 프로세스 확인"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(str(arg) for arg in cmdline if arg)
                        # run_rdg.py 또는 RDG_v1.py 둘 다 확인
                        if 'run_rdg.py' in cmdline_str or 'RDG_v1.py' in cmdline_str:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
        except Exception as e:
            # psutil 없으면 ps 명령어 사용 (Linux/Unix)
            try:
                result = os.popen('ps aux | grep -E "[r]un_rdg.py|RDG_v1.py"').read()
                return bool(result.strip())
            except:
                return False

    def is_running(self) -> bool:
        """RDG 프로세스 실행 여부 확인"""
        if self._process is None:
            return False

        # poll()이 None이면 아직 실행 중
        return self._process.poll() is None

    def _parse_log_stats(self) -> Dict:
        """로그 파일에서 통계 파싱"""
        log_file = self._get_latest_log_file()
        print(f"[DEBUG] Looking for log file at: {log_file}")
        print(f"[DEBUG] Log file exists: {log_file.exists()}")

        if not log_file.exists():
            print(f"[DEBUG] Log file not found, returning empty stats")
            return self._get_empty_stats()

        try:
            # 로그 파일의 마지막 통계 리포트 읽기
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 마지막 통계 블록 찾기 (역순으로 검색)
            stats_block = []
            found_separator = False

            for line in reversed(lines):
                if '=' * 60 in line:
                    if found_separator:
                        break
                    found_separator = True
                elif found_separator:
                    stats_block.insert(0, line)

            # 통계 파싱
            sent = 0
            success = 0
            fail = 0
            actual_rps = 0.0
            success_rate = 0.0
            uptime_sec = 0.0

            print(f"[DEBUG] Found {len(stats_block)} lines in stats block")

            for line in stats_block:
                # 경과 시간: 120.50초
                if match := re.search(r'경과 시간:\s*([\d.]+)초', line):
                    uptime_sec = float(match.group(1))
                # 전송: 1205 | 성공: 1198 | 실패: 7
                elif match := re.search(r'전송:\s*(\d+)\s*\|\s*성공:\s*(\d+)\s*\|\s*실패:\s*(\d+)', line):
                    sent = int(match.group(1))
                    success = int(match.group(2))
                    fail = int(match.group(3))
                # 실제 RPS: 10.04 | 성공률: 99.42%
                elif match := re.search(r'실제 RPS:\s*([\d.]+)\s*\|\s*성공률:\s*([\d.]+)%', line):
                    actual_rps = float(match.group(1))
                    success_rate = float(match.group(2))

            print(f"[DEBUG] Parsed stats: sent={sent}, success={success}, fail={fail}")

            return {
                "uptime_sec": uptime_sec,
                "sent": sent,
                "ok": success,
                "fail": fail,
                "success_rate": success_rate,
                "actual_rps": actual_rps,
                "avg_latency_ms": 0.0,  # RDG_v1.py에서는 평균 레이턴시를 로그에 출력하지 않음
                "in_flight": 0,  # 실시간 추적 불가
                "last_tick": time.time()
            }

        except Exception as e:
            print(f"Error parsing log: {e}")
            return self._get_empty_stats()

    def _get_empty_stats(self) -> Dict:
        """빈 통계 반환"""
        return {
            "uptime_sec": 0,
            "sent": 0,
            "ok": 0,
            "fail": 0,
            "success_rate": 0.0,
            "actual_rps": 0.0,
            "avg_latency_ms": 0.0,
            "in_flight": 0,
            "last_tick": 0.0
        }

# 싱글톤
runner = RDGRunner()
