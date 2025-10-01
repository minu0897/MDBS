# config/__init__.py
"""
config 패키지 초기화.
이 모듈을 통해 외부에서 load_config를 바로 임포트할 수 있게 함.
"""
from .settings import load_config

__all__ = ["load_config"]
