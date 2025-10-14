# services/docker_stats_service.py
import os
import re
import time
import threading
from typing import Any, Dict, List, Tuple
import docker


class _DockerStatsCollector:
    """
    docker.sock을 통해 컨테이너 메트릭을 주기적으로 수집하여 캐시에 보관.
    - stream=False 1-shot stats
    - CPU%: (delta total / delta system) * ncpu * 100
    - Net/Block IO: 인터페이스/항목 합산
    """
    def __init__(self):
        self.base_url = os.getenv("DOCKER_SOCK", "unix://var/run/docker.sock")
        self.poll_sec = float(os.getenv("STATS_POLL_SEC", "2"))
        self.name_filter = os.getenv("NAME_FILTER", "")  # e.g. "mysql|postgres|oracle|mongo|mongod"
        self.label_key = os.getenv("LABEL_KEY", "")      # e.g. "com.mdbs.role"
        self.label_val = os.getenv("LABEL_VAL", "dbms")

        self.client = docker.DockerClient(base_url=self.base_url)
        self._cache: Dict[str, Any] = {"ts": 0.0, "data": []}
        self._started = False
        self._stop = False
        self._lock = threading.Lock()

    # ---------- public ----------
    def start_once(self):
        if self._started:
            return
        self._started = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def get_cached(self) -> Dict[str, Any]:
        with self._lock:
            # 얕은 복사로 충분
            return {"ts": self._cache["ts"], "data": list(self._cache["data"])}

    # ---------- internal ----------
    def _loop(self):
        while not self._stop:
            try:
                data = self._collect_once()
                with self._lock:
                    self._cache["data"] = data
                    self._cache["ts"] = time.time()
            except Exception as e:
                with self._lock:
                    self._cache["data"] = [{"error": f"collector_failed: {e}"}]
                    self._cache["ts"] = time.time()
            time.sleep(self.poll_sec)

    def _collect_once(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for c in self.client.containers.list(all=True):
            if not self._match_filters(c):
                continue
            try:
                stat = c.stats(stream=False)
                cpu = round(self._cpu_percent(stat), 2)
                mem_u, mem_l, mem_p = self._mem_usage(stat)
                rx, tx = self._sum_net_io(stat)
                br, bw = self._sum_block_io(stat)
                rows.append({
                    "name": c.name,
                    "id": c.short_id,
                    "state": c.status,
                    "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                    "cpu": cpu,                          # %
                    "mem_bytes": mem_u,                  # bytes
                    "mem_limit": mem_l,                  # bytes
                    "mem_perc": round(mem_p, 2),         # %
                    "net_rx": rx,                        # bytes
                    "net_tx": tx,                        # bytes
                    "block_read": br,                    # bytes
                    "block_write": bw,                   # bytes
                })
            except Exception as e:
                rows.append({
                    "name": c.name, "id": c.short_id, "state": "error", "error": str(e)
                })
        return rows

    def _match_filters(self, container) -> bool:
        if self.name_filter and not re.search(self.name_filter, container.name):
            return False
        if self.label_key:
            labels = (container.attrs or {}).get("Config", {}).get("Labels", {}) or {}
            if labels.get(self.label_key) != self.label_val:
                return False
        return True

    @staticmethod
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

    @staticmethod
    def _mem_usage(stat: Dict[str, Any]) -> Tuple[int, int, float]:
        ms = stat.get("memory_stats", {}) or {}
        usage = ms.get("usage") or 0
        limit = ms.get("limit") or 1
        perc = (usage / limit * 100.0) if limit else 0.0
        return usage, limit, perc

    @staticmethod
    def _sum_net_io(stat: Dict[str, Any]) -> Tuple[int, int]:
        rx = tx = 0
        for _, v in (stat.get("networks") or {}).items():
            rx += v.get("rx_bytes", 0) or 0
            tx += v.get("tx_bytes", 0) or 0
        return rx, tx

    @staticmethod
    def _sum_block_io(stat: Dict[str, Any]) -> Tuple[int, int]:
        r = w = 0
        for ent in (stat.get("blkio_stats", {}).get("io_service_bytes_recursive") or []):
            op = (ent.get("op") or "").lower()
            val = ent.get("value") or 0
            if op == "read":
                r += val
            elif op == "write":
                w += val
        return r, w


# 모듈 레벨 싱글턴
collector = _DockerStatsCollector()