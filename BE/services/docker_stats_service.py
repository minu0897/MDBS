# BE/services/docker_stats_service.py
import os, re, time, threading
from typing import Any, Dict, List, Tuple
from urllib.parse import quote_plus

# SDK 경로
import docker
from docker.errors import DockerException

# REST Fallback 경로
import requests
try:
    from requests_unixsocket import UnixAdapter
except Exception:
    UnixAdapter = None


def _cpu_percent(stat: Dict[str, Any]) -> float:
    cs = stat.get("cpu_stats", {}) or {}
    ps = stat.get("precpu_stats", {}) or {}
    cu = cs.get("cpu_usage", {}) or {}
    pu = ps.get("cpu_usage", {}) or {}
    sys = cs.get("system_cpu_usage", 0) or 0
    pys = ps.get("system_cpu_usage", 0) or 0
    cpu_delta = (cu.get("total_usage") or 0) - (pu.get("total_usage") or 0)
    sys_delta = sys - pys
    ncpu = len(cu.get("percpu_usage") or []) or 1
    if cpu_delta > 0 and sys_delta > 0:
        return (cpu_delta / sys_delta) * ncpu * 100.0
    return 0.0


def _mem_usage(stat: Dict[str, Any]) -> Tuple[int, int, float]:
    ms = stat.get("memory_stats", {}) or {}
    usage = ms.get("usage") or 0
    limit = ms.get("limit") or 1
    perc = (usage / limit * 100.0) if limit else 0.0
    return usage, limit, perc


def _sum_net_io(stat: Dict[str, Any]) -> Tuple[int, int]:
    rx = tx = 0
    for _, v in (stat.get("networks") or {}).items():
        rx += v.get("rx_bytes", 0) or 0
        tx += v.get("tx_bytes", 0) or 0
    return rx, tx


def _sum_block_io(stat: Dict[str, Any]) -> Tuple[int, int]:
    r = w = 0
    arr = (stat.get("blkio_stats", {}).get("io_service_bytes_recursive") or [])
    for ent in arr:
        op = (ent.get("op") or "").lower()
        val = ent.get("value") or 0
        if op == "read":
            r += val
        elif op == "write":
            w += val
    return r, w


class _DockerStatsCollector:
    def __init__(self):
        # 환경변수 보정
        raw = (os.getenv("DOCKER_SOCK", "unix:///var/run/docker.sock") or "").strip()
        if raw.startswith("unix://") and not raw.startswith("unix:///"):
            raw = raw.replace("unix://", "unix:///", 1)

        self.base_url = raw                               # docker SDK용
        self.sock_path = "/var/run/docker.sock"           # REST fallback용
        self.poll_sec = float(os.getenv("STATS_POLL_SEC", "2"))
        self.name_filter = os.getenv("NAME_FILTER", "")   # 예: mysql|postgres|oracle|mongo
        self.label_key = os.getenv("LABEL_KEY", "")       # 선택
        self.label_val = os.getenv("LABEL_VAL", "dbms")   # 선택

        self.client = None        # docker SDK client
        self._sess = None         # REST fallback session
        self._cache: Dict[str, Any] = {"ts": 0.0, "data": []}
        self._started = False
        self._stop = False
        self._lock = threading.Lock()

    # ---- filters ----
    def _match_name(self, name: str) -> bool:
        if self.name_filter and not re.search(self.name_filter, name):
            return False
        return True

    def _match_labels(self, labels: Dict[str, str]) -> bool:
        if self.label_key:
            if (labels or {}).get(self.label_key) != self.label_val:
                return False
        return True

    # ---- client ensure (SDK → fallback) ----
    def _ensure_client(self):
        if self.client is not None or self._sess is not None:
            return

        # 1) docker SDK 시도
        try:
            self.client = docker.DockerClient(base_url=self.base_url)
            self.client.ping()
            return
        except Exception as e1:
            self.client = None

        # 2) REST Fallback (requests_unixsocket)
        if UnixAdapter is None:
            with self._lock:
                self._cache["data"] = [{
                    "error": "docker_client_init_failed",
                    "detail": "requests-unixsocket not available"
                }]
                self._cache["ts"] = time.time()
            raise RuntimeError("requests-unixsocket not available")

        s = requests.Session()
        s.mount("http+unix://", UnixAdapter())  # ❗️인자 없음
        base = f"http+unix://{quote_plus(self.sock_path)}"  # ex) http+unix://%2Fvar%2Frun%2Fdocker.sock
        try:
            r = s.get(f"{base}/_ping", timeout=2)
            ok = (r.status_code == 200 and r.text.strip().upper() == "OK")
            if not ok:
                raise RuntimeError(f"_ping failed: {r.status_code} {r.text}")
            self._sess = s
            self._rest_base = base  # 나중에 재사용
        except Exception as e2:
            with self._lock:
                self._cache["data"] = [{
                    "error": "docker_client_init_failed",
                    "detail": f"SDK fail + REST fallback fail: {type(e2).__name__}: {e2}"
                }]
                self._cache["ts"] = time.time()
            raise

    # ---- background loop ----
    def start_once(self):
        if self._started:
            return
        self._started = True

        # 빠른 재시도 3회
        for _ in range(3):
            try:
                self._ensure_client()
                break
            except Exception:
                time.sleep(0.2)

        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while not self._stop:
            try:
                if self.client is None and self._sess is None:
                    self._ensure_client()
                data = self._collect_once()
                with self._lock:
                    self._cache["data"] = data
                    self._cache["ts"] = time.time()
            except Exception as e:
                with self._lock:
                    self._cache["data"] = [{"error": f"collector_failed: {e}"}]
                    self._cache["ts"] = time.time()
            time.sleep(self.poll_sec)

    # ---- collect once (SDK 우선, 실패시 REST) ----
    def _collect_once(self) -> List[Dict[str, Any]]:
        # SDK 경로
        if self.client is not None:
            rows: List[Dict[str, Any]] = []
            for c in self.client.containers.list(all=True):
                # 라벨 필터
                labels = (c.attrs or {}).get("Config", {}).get("Labels", {}) or {}
                if not self._match_labels(labels):
                    continue
                # 이름 필터
                if not self._match_name(c.name):
                    continue

                try:
                    stat = c.stats(stream=False)
                    cpu = round(_cpu_percent(stat), 2)
                    mem_used, mem_limit, mem_perc = _mem_usage(stat)
                    net_rx, net_tx = _sum_net_io(stat)
                    blk_r, blk_w = _sum_block_io(stat)
                    rows.append({
                        "name": c.name,
                        "id": c.short_id,
                        "state": c.status,
                        "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                        "cpu": cpu,
                        "mem_bytes": mem_used,
                        "mem_limit": mem_limit,
                        "mem_perc": round(mem_perc, 2),
                        "net_rx": net_rx,
                        "net_tx": net_tx,
                        "block_read": blk_r,
                        "block_write": blk_w
                    })
                except Exception as e:
                    rows.append({"name": c.name, "id": c.short_id, "state": "error", "error": str(e)})
            return rows

        # REST 경로 (SDK 실패 시)
        if self._sess is None:
            # 캐시에 이미 상세 사유 있을 수 있음
            return self._cache["data"] or [{"error": "docker_client_not_ready"}]

        rows: List[Dict[str, Any]] = []
        base = getattr(self, "_rest_base", f"http+unix://{quote_plus(self.sock_path)}")

        # 1) 컨테이너 목록
        r = self._sess.get(f"{base}/containers/json?all=1", timeout=3)
        r.raise_for_status()
        containers = r.json()

        for c in containers:
            name = (c.get("Names") or [""])[0].lstrip("/") if c.get("Names") else c.get("Id")[:12]
            if not self._match_name(name):
                continue
            labels = c.get("Labels", {}) or {}
            if not self._match_labels(labels):
                continue

            cid = c.get("Id")
            image = c.get("Image")
            state = c.get("State")
            try:
                r2 = self._sess.get(f"{base}/containers/{cid}/stats?stream=false", timeout=3)
                r2.raise_for_status()
                stat = r2.json()
                cpu = round(_cpu_percent(stat), 2)
                mem_used, mem_limit, mem_perc = _mem_usage(stat)
                net_rx, net_tx = _sum_net_io(stat)
                blk_r, blk_w = _sum_block_io(stat)
                rows.append({
                    "name": name,
                    "id": cid[:12],
                    "state": state,
                    "image": image,
                    "cpu": cpu,
                    "mem_bytes": mem_used,
                    "mem_limit": mem_limit,
                    "mem_perc": round(mem_perc, 2),
                    "net_rx": net_rx,
                    "net_tx": net_tx,
                    "block_read": blk_r,
                    "block_write": blk_w
                })
            except Exception as e:
                rows.append({"name": name, "id": cid[:12], "state": state, "error": str(e)})
        return rows

    # ---- public API ----
    def get_cached(self) -> Dict[str, Any]:
        with self._lock:
            return {"ts": self._cache["ts"], "data": list(self._cache["data"])}

    def stop(self):
        self._stop = True


collector = _DockerStatsCollector()
