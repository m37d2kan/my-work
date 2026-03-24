from fastapi import APIRouter
from app.config import settings
from app.runtime import runtime_state

router = APIRouter()


@router.post("/control/auto-on")
async def auto_on():
    settings.auto_enabled = True
    runtime_state.add_log("CONTROL", "AUTO ON")
    return {"ok": True, "auto_enabled": True}


@router.post("/control/auto-off")
async def auto_off():
    settings.auto_enabled = False
    runtime_state.add_log("CONTROL", "AUTO OFF")
    return {"ok": True, "auto_enabled": False}


@router.post("/control/emergency-stop")
async def emergency_stop():
    runtime_state.order_state.emergency_stop = True
    settings.auto_enabled = False
    runtime_state.add_log("CONTROL", "EMERGENCY STOP")
    return {"ok": True}


@router.post("/control/recover")
async def recover():
    runtime_state.order_state.emergency_stop = False
    runtime_state.add_log("CONTROL", "RECOVER from emergency stop")
    return {"ok": True}


@router.post("/control/cancel-all")
async def cancel_all():
    from app.scheduler import _runner
    if _runner:
        await _runner.order_manager.cancel_all_entry_orders()
    runtime_state.add_log("CONTROL", "CANCEL ALL entry orders")
    return {"ok": True}
