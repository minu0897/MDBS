# services/mongo_tx_service.py
from typing import Any, Dict, Tuple
from decimal import Decimal
from bson.decimal128 import Decimal128
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from db.router import get_adapter



# ---------- 보조 ----------
def _dec(v: Any) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v))

def _d128(v: Any) -> Decimal128:
    return Decimal128(_dec(v))

def _neg_d128(v) -> Decimal128:
    d = v.to_decimal() if isinstance(v, Decimal128) else _dec(v)
    return Decimal128(-d)

def _idem_insert(col, doc: dict, unique_filter: Dict[str, Any]) -> Tuple[bool, str]:
    """
    멱등 insert.
    - unique_filter에 해당 문서가 이미 있으면 'ALREADY'
    - 없으면 insert 시도, Unique 충돌은 'ALREADY'로 간주
    """
    old = col.find_one(unique_filter, {"_id": 1})
    if old:
        return False, "ALREADY"
    try:
        col.insert_one(doc)
        return True, "CREATED"
    except DuplicateKeyError:
        return False, "ALREADY"

class MongoTxService:
    """
    싱글 노드 Mongo에서도 동작하는 '프로시저성' 서비스.
    - 세션/트랜잭션 미사용
    - 문서 단위 원자 연산 + 멱등키(Unique)로 정합성 확보
    collections:
      accounts(_id, balance:Decimal128, hold_amount:Decimal128)
      transactions(idempotency_key:Unique, status, type, ...)
      holds(idempotency_key:Unique, status, account_id, amount)
      ledger_entries(Unique(txn_id, account_id, amount))
    """

    def __init__(self):
        mongo = get_adapter("mongo")
        self.client = mongo.client
        self.db = mongo.db
        self.ACC    = self.db.accounts
        self.TXN    = self.db.transactions
        self.HOLD   = self.db.holds
        self.LEDGER = self.db.ledger_entries

    # 최초 1회만 호출하면 좋은 인덱스 (있으면 OK)
    def ensure_indexes(self):
        self.TXN.create_index("idempotency_key", unique=True)
        self.HOLD.create_index("idempotency_key", unique=True)
        self.LEDGER.create_index([("txn_id", 1), ("account_id", 1), ("amount", 1)], unique=True)

    # 1) 송금 보류(sp_remittance_hold 대체)
    def remittance_hold(self, body: Dict[str, Any]):
        src       = body["src_account_id"]
        dst       = body["dst_account_id"]
        dst_bank  = body.get("dst_bank", "")
        amount128 = _d128(body["amount"])
        amount    = _dec(body["amount"])
        idem      = body["idempotency_key"]
        typ       = body.get("type", "1")  # 1: 내부, 2: 외부송금, 3: 외부수취
        c_at = datetime.utcnow()

        # txn 멱등 생성
        _idem_insert(self.TXN, {
            "type": typ, 
            "status": "1",
            "src_account_id": src, 
            "dst_account_id": dst, 
            "dst_bank": dst_bank,
            "amount": amount128, 
            "idempotency_key": idem,
            "created_at": c_at
        }, {"idempotency_key": idem})

        tx = self.TXN.find_one({"idempotency_key": idem}, {"_id": 1})
        txn_id = tx["_id"]

        # (balance - hold_amount) >= amount 조건부로 hold_amount 증가
        res = self.ACC.update_one(
            {"_id": src, "$expr": {"$gte": [{"$subtract": ["$balance", "$hold_amount"]}, amount128]}},
            {"$inc": {"hold_amount": amount128}}
        )
        if res.modified_count != 1:
            self.TXN.update_one({"_id": txn_id}, {"$set": {"status": "5"}})  # 잔액부족
            return {"txn_id": str(txn_id), "status": "5"}

        # holds 멱등 생성(이미 있으면 OK)
        _idem_insert(self.HOLD, {
            "account_id": src, "amount": amount128, "status": "1",
            "idempotency_key": idem,
            "created_at": c_at
        }, {"idempotency_key": idem})

        self.TXN.update_one({"_id": txn_id}, {"$set": {"status": "1"}})
        return {"txn_id": str(txn_id), "status": "1"}

    # 2) 수금 준비(sp_receive_prepare 대체)
    def receive_prepare(self, body: Dict[str, Any]):
        src       = body["src_account_id"]
        dst       = body["dst_account_id"]
        dst_bank  = body.get("dst_bank", "")
        amount128 = _d128(body["amount"])
        idem      = body["idempotency_key"]
        typ       = body.get("type", "3")
        c_at = datetime.utcnow()

        _idem_insert(self.TXN, {
            "type": typ, "status": "1",
            "src_account_id": src, "dst_account_id": dst, "dst_bank": dst_bank,
            "amount": amount128, "idempotency_key": idem,
            "created_at": c_at
        }, {"idempotency_key": idem})

        tx = self.TXN.find_one({"idempotency_key": idem}, {"_id": 1})
        txn_id = tx["_id"]

        if self.ACC.count_documents({"_id": dst}) == 0:
            self.TXN.update_one({"_id": txn_id}, {"$set": {"status": "6"}})
            return {"txn_id": str(txn_id), "status": "6"}

        return {"txn_id": str(txn_id), "status": "1"}

    # 3) 출금 확정(동일 은행) — hold↓ + balance↓ + 분개(-)
    def confirm_debit_local(self, body: Dict[str, Any]):
        idem = body["idempotency_key"]

        tx = self.TXN.find_one({"idempotency_key": idem})
        if not tx:
            return {"status": "1", "result": "TX_NOT_FOUND"}

        txn_id = tx["_id"]
        src    = tx["src_account_id"]
        amt128 = tx["amount"] if isinstance(tx["amount"], Decimal128) else _d128(tx["amount"])
        amt    = amt128.to_decimal()
        c_at = datetime.utcnow()

        hold = self.HOLD.find_one({"idempotency_key": idem})
        if not hold:
            return {"txn_id": str(txn_id), "status": "1", "result": "HOLD_NOT_FOUND"}
        if hold.get("status") == "3":
            return {"txn_id": str(txn_id), "status": "1", "result": "HOLD_RELEASED"}
        if hold.get("status") == "2":
            return {"txn_id": str(txn_id), "status": "2", "result": "ALREADY_CONFIRMED"}

        # hold_amount >= amt 조건부로 hold↓, balance↓
        res = self.ACC.update_one(
            {"_id": src, "hold_amount": {"$gte": amt}},
            {"$inc": {"hold_amount": -amt128, "balance": -amt128}}
        )
        if res.modified_count != 1:
            return {"txn_id": str(txn_id), "status": "1", "result": "CONCURRENCY_FAIL"}

        # 분개(음수) 멱등
        _idem_insert(self.LEDGER,
            {"txn_id": txn_id, "account_id": src, "amount": -amt128,"created_at": c_at},
            {"txn_id": txn_id, "account_id": src, "amount": -amt,"created_at": c_at}
        )

        self.HOLD.update_one({"idempotency_key": idem}, {"$set": {"status": "2"}})
        self.TXN.update_one({"_id": txn_id}, {"$set": {"status": "2"}})
        return {"txn_id": str(txn_id), "status": "2", "result": "OK"}

    # 4) 입금 확정(동일 은행) — balance↑ + 분개(+)
    def confirm_credit_local(self, body: Dict[str, Any]):
        idem = body["idempotency_key"]

        tx = self.TXN.find_one({"idempotency_key": idem})
        if not tx:
            return {"status": "1", "result": "TX_NOT_FOUND"}

        txn_id = tx["_id"]
        dst    = tx["dst_account_id"]
        amt128 = tx["amount"] if isinstance(tx["amount"], Decimal128) else _d128(tx["amount"])
        amt    = amt128.to_decimal()
        c_at = datetime.utcnow()

        # 이미 분개 있으면 멱등 OK
        if self.LEDGER.find_one({"txn_id": txn_id, "account_id": dst, "amount": amt}):
            self.TXN.update_one({"_id": txn_id}, {"$set": {"status": "2"}})
            return {"txn_id": str(txn_id), "status": "2", "result": "ALREADY_POSTED"}

        # balance↑
        self.ACC.update_one({"_id": dst}, {"$inc": {"balance": amt128}})

        # 분개(양수) 멱등
        _idem_insert(self.LEDGER,
            {"txn_id": txn_id, "account_id": dst, "amount": amt128,"created_at": c_at},
            {"txn_id": txn_id, "account_id": dst, "amount": amt,"created_at": c_at}
        )

        self.TXN.update_one({"_id": txn_id}, {"$set": {"status": "2"}})
        return {"txn_id": str(txn_id), "status": "2", "result": "OK"}

    # 5) 내부 이체 확정 — 출금(보류/무보류) + 입금 + 양쪽 분개
    def transfer_confirm_internal(self, body: Dict[str, Any]):
        idem = body["idempotency_key"]

        tx = self.TXN.find_one({"idempotency_key": idem})
        if not tx:
            return {"status": "1", "result": "TX_NOT_FOUND"}

        txn_id = tx["_id"]
        src    = tx["src_account_id"]
        dst    = tx["dst_account_id"]
        amt128 = tx["amount"] if isinstance(tx["amount"], Decimal128) else _d128(tx["amount"])
        amt    = amt128.to_decimal()
        c_at = datetime.utcnow()

        hold = self.HOLD.find_one({"idempotency_key": idem})
        if hold and hold.get("status") == "2":
            return {"status": "2", "result": "ALREADY_CONFIRMED"}

        # 출금(보류O: hold↓+balance↓, 보류X: balance↓)
        if hold:
            res = self.ACC.update_one(
                {"_id": src, "hold_amount": {"$gte": amt}},
                {"$inc": {"hold_amount": -amt128, "balance": -amt128}}
            )
            if res.modified_count != 1:
                return {"status": "1", "result": "CONCURRENCY_FAIL"}
            self.HOLD.update_one({"idempotency_key": idem}, {"$set": {"status": "2"}})
        else:
            res = self.ACC.update_one(
                {"_id": src, "balance": {"$gte": amt}},
                {"$inc": {"balance": -amt128}}
            )
            if res.modified_count != 1:
                return {"status": "1", "result": "INSUFFICIENT_FUNDS"}

        # 입금
        self.ACC.update_one({"_id": dst}, {"$inc": {"balance": amt128}})

        # 분개 멱등 (음수/양수)
        _idem_insert(self.LEDGER,
            {"txn_id": txn_id, "account_id": src, "amount": -amt128,"created_at": c_at},
            {"txn_id": txn_id, "account_id": src, "amount": -amt,"created_at": c_at}
        )
        _idem_insert(self.LEDGER,
            {"txn_id": txn_id, "account_id": dst, "amount":  amt128,"created_at": c_at},
            {"txn_id": txn_id, "account_id": dst, "amount":  amt,"created_at": c_at}
        )

        self.TXN.update_one({"_id": txn_id}, {"$set": {"status": "2"}})
        return {"status": "2", "result": "OK"}
