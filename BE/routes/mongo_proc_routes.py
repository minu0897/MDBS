# routes/mongo_proc_routes.py
from flask import Blueprint, request
from services.mongo_tx_service import MongoTxService
from utils.response import ok, fail

mongo_bp = Blueprint("mongo_proc", __name__)

@mongo_bp.post("/init/indexes")
def init_indexes():
    try:
        MongoTxService().ensure_indexes()#인덱스 있는지 체크
        return ok({"initialized": True})
    except Exception as e:
        return fail(str(e), 400)

@mongo_bp.post("/remittance/hold")
def remittance_hold():
    try:
        svc = MongoTxService()
        return ok(svc.remittance_hold(request.get_json(force=True)))
    except Exception as e:
        return fail(str(e), 400)

@mongo_bp.post("/receive/prepare")
def receive_prepare():
    try:
        svc = MongoTxService()
        return ok(svc.receive_prepare(request.get_json(force=True)))
    except Exception as e:
        return fail(str(e), 400)

@mongo_bp.post("/confirm/debit/local")
def confirm_debit_local():
    try:
        svc = MongoTxService()
        return ok(svc.confirm_debit_local(request.get_json(force=True)))
    except Exception as e:
        return fail(str(e), 400)

@mongo_bp.post("/confirm/credit/local")
def confirm_credit_local():
    try:
        svc = MongoTxService()
        return ok(svc.confirm_credit_local(request.get_json(force=True)))
    except Exception as e:
        return fail(str(e), 400)

@mongo_bp.post("/transfer/confirm/internal")
def transfer_confirm_internal():
    try:
        svc = MongoTxService()
        return ok(svc.transfer_confirm_internal(request.get_json(force=True)))
    except Exception as e:
        return fail(str(e), 400)
