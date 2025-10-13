# rdg_runner.py
import asyncio
import random
import time
import uuid
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import aiohttp

DBS = ["mysql", "postgres", "oracle", "mongo"]
BASE_URL = "http://127.0.0.1:5000"  # 고정

@dataclass
class RDGConfig:
    rps: int = 10                  # 초당 요청 수
    concurrent: int = 50           # 동시 연결 제한
    allow_same_db: bool = True    # 송금/수금 DB가 같아도 허용할지
    src_accounts: List[int] = field(default_factory=lambda: list(range(200000, 200200)))
    dst_accounts: List[int] = field(default_factory=lambda: list(range(200000, 200200)))
    min_amount: int = 1_000
    max_amount: int = 100_000

@dataclass
class RDGStats:
    started_at: float = 0.0
    last_tick: float = 0.0
    sent: int = 0
    ok: int = 0
    fail: int = 0
    in_flight: int = 0
    lat_sum_ms: float = 0.0

    def snapshot(self) -> Dict:
        avg_lat = (self.lat_sum_ms / self.ok) if self.ok else 0.0
        return dict(
            uptime_sec=time.time() - self.started_at if self.started_at else 0,
            sent=self.sent, ok=self.ok, fail=self.fail,
            in_flight=self.in_flight, avg_latency_ms=round(avg_lat, 2),
            last_tick=self.last_tick
        )

class RDGRunner:
    def __init__(self):
        self._lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop = threading.Event()
        self._cfg: Optional[RDGConfig] = None
        self._stats = RDGStats()

    # ---------- public ----------
    def start(self, cfg: RDGConfig):
        with self._lock:
            if self.is_running():
                raise RuntimeError("RDG is already running")
            self._cfg = cfg
            self._stop.clear()
            self._stats = RDGStats(started_at=time.time())
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            if not self.is_running():
                return
            self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        with self._lock:
            self._thread = None
            self._loop = None

    def status(self) -> Dict:
        with self._lock:
            running = self.is_running()
            cfg = self._cfg.__dict__ if self._cfg else None
            return dict(running=running, cfg=cfg, stats=self._stats.snapshot(), base_url=BASE_URL)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ---------- internal ----------
    def _run_loop(self):
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._main())
        except Exception:
            pass
        finally:
            try:
                if self._loop and not self._loop.is_closed():
                    self._loop.run_until_complete(self._loop.shutdown_asyncgens())
                    self._loop.close()
            except:
                pass

    async def _main(self):
        assert self._cfg, "config required"
        sem = asyncio.Semaphore(self._cfg.concurrent)
        conn = aiohttp.TCPConnector(limit=self._cfg.concurrent)
        async with aiohttp.ClientSession(connector=conn) as session:
            while not self._stop.is_set():
                tick_start = time.time()
                self._stats.last_tick = tick_start
                tasks = []
                for _ in range(self._cfg.rps):
                    await sem.acquire()
                    task = asyncio.create_task(self._single_request(session))
                    task.add_done_callback(lambda _t: sem.release())
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)
                elapsed = time.time() - tick_start
                sleep_left = max(0, 1.0 - elapsed)
                await asyncio.sleep(sleep_left)

    async def _single_request(self, session: aiohttp.ClientSession):
        self._stats.in_flight += 1
        t0 = time.time()
        try:
            src_db, dst_db = self._pick_two_dbs()
            payload = self._make_payload(src_db, dst_db)

            url = f"{BASE_URL}/db/proc/exec"  # 고정

            async with session.post(url, json=payload, timeout=10) as resp:
                _ = await resp.text()
                self._stats.sent += 1
                if 200 <= resp.status < 300:
                    self._stats.ok += 1
                else:
                    self._stats.fail += 1
        except Exception:
            self._stats.sent += 1
            self._stats.fail += 1
        finally:
            dt_ms = (time.time() - t0) * 1000.0
            self._stats.lat_sum_ms += dt_ms
            self._stats.in_flight -= 1

    def _pick_two_dbs(self):
        src = random.choice(DBS)
        dst = random.choice(DBS)
        if not self._cfg.allow_same_db:
            while dst == src:
                dst = random.choice(DBS)
        return src, dst

    def _make_payload(self, src_db: str, dst_db: str) -> Dict:
        src_acc = random.choice(self._cfg.src_accounts)
        dst_acc = random.choice(self._cfg.dst_accounts)
        amount = random.randint(self._cfg.min_amount, self._cfg.max_amount)
        idem = str(uuid.uuid4())

        hold_args = [src_acc, dst_acc, "EXT", amount, idem, "1"]
        settle_args = [None, idem]

        src_payload = dict(db=src_db, kind="proc", name="sp_remittance_hold", args=hold_args)
        dst_payload = dict(db=dst_db, kind="proc", name="sp_remittance_settle", args=settle_args)

        return dict(
            op="remit",
            src=src_payload,
            dst=dst_payload,
            meta=dict(idempotency_key=idem, ts=int(time.time()))
        )

# 싱글톤
runner = RDGRunner()
