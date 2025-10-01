# tests/test_system_routes.py
import os
import sys
import json
import pytest
from app import app as flask_app

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

def test_status(client):
    resp = client.get("/system/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    keys = data["data"].keys()
    for k in ["cpu_percent", "mem", "disk", "loadavg"]:
        assert k in keys

def test_run_py_demo(client):
    # scripts/demo_task.py 실행
    resp = client.post("/system/run-py", json={
        "script": "demo_task.py",
        "args": ["--msg", "pytest", "--sleep", "0.0"],
        "timeout": 5
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["data"]["returncode"] == 0
    assert "pytest" in data["data"]["stdout"]

def test_exec_echo(client):
    # OS에 따라 echo 유무가 다를 수 있으나 대부분 기본 제공
    # 윈도우 환경에선 'cmd' 사용이 필요하지만, 서버/리눅스 가정
    resp = client.post("/system/exec", json={
        "cmd": "echo",
        "args": ["hello"],
        "timeout": 5
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["data"]["returncode"] == 0
    assert "hello" in data["data"]["stdout"]
