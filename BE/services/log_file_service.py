# services/log_file_service.py
import os
from pathlib import Path
from typing import List, Dict

# 두 개의 로그 디렉토리
LOG_DIRS = [
    Path("/home/kmw/MDBS/BE/scripts/temp_log"),
    Path("/home/kmw/MDBS/BE/scripts"),
]

def get_log_files() -> List[Dict[str, any]]:
    """
    두 개의 디렉토리에서 로그 파일 목록 조회
    - /home/kmw/MDBS/BE/scripts/temp_log/
    - /home/kmw/MDBS/BE/scripts/

    Returns:
        [
            {
                "filename": "rdg_log_250124_143022.log",
                "size": 1024000,
                "modified": 1706083822.0,
                "path": "/home/kmw/MDBS/BE/scripts/temp_log"
            },
            ...
        ]
    """
    log_files = []

    for log_dir in LOG_DIRS:
        if not log_dir.exists():
            continue

        for file_path in log_dir.glob("*.log"):
            if file_path.is_file():
                stat = file_path.stat()
                log_files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "path": str(log_dir)
                })

    # 최신 파일 먼저
    log_files.sort(key=lambda x: x["modified"], reverse=True)

    return log_files

def get_log_file_path(filename: str) -> Path:
    """
    로그 파일의 안전한 경로 반환 (디렉토리 탈출 방지)
    두 개의 디렉토리에서 파일을 찾음

    Args:
        filename: 로그 파일명 (예: "rdg_log_250124_143022.log")

    Returns:
        Path 객체

    Raises:
        ValueError: 잘못된 파일명 또는 파일을 찾을 수 없음
    """
    # 파일명 검증 (경로 구분자 금지)
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("Invalid filename")

    # 두 디렉토리에서 파일 찾기
    for log_dir in LOG_DIRS:
        file_path = (log_dir / filename).resolve()

        # 디렉토리 탈출 방지
        if not str(file_path).startswith(str(log_dir.resolve())):
            continue

        if file_path.exists() and file_path.is_file():
            return file_path

    raise ValueError("File not found")
