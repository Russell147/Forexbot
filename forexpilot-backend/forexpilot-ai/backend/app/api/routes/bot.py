from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import BotLog, Notification, Strategy, Trade, TradingPair, TradingSignal
from app.schemas import EmergencyIn
from app.services.engine_status import get_engine_status
from app.services.state import (add_log, add_notification, engine_online, get_bot, get_risk, iso, ser_risk, ser_trade)

router = APIRouter(tags=["bot"])


def _status(db: Session) -> dict:
    b = get_bot(db)
    return {"desired": b.desired_state, "actual": b.actual_state, "engineOnline": engine_online(b), "mt5Connected": b.mt5_connected,
            "heartbeat": iso(b.heartbeat), "run": b.actual_state == "running", "emg": b.desired_state == "emergency",
            "liveBlocked": b.actual_state == "blocked_live"}


def _signals(db: Session) -> list[dict]:
    rows = db.query(TradingSignal).order_by(TradingSignal.id.desc()).limit(60).all()
    return [{"symbol": s.symbol, "strategy": s.strategy, "timeframe": s.timeframe, "direction": s.direction,
             "status": s.status, "reason": s.reason, "time": iso(s.created_at)} for s in rows]


@router.get("/bot/status")
def status(db: Session = Depends(get_db)):
    return _status(db)


@router.get("/engine/health")
def engine_health(refresh: bool = False):
    """Proxied engine health so the browser never needs the engine's address."""
    return get_engine_status(force=refresh)


@router.post("/bot/start")
def start(db: Session = Depends(get_db)):
    b = get_bot(db)
    if not engine_online(b):
        raise HTTPException(409, "Trading engine is offline. Start trading-engine/main.py on the MT5 machine first.")
    if b.actual_state == "blocked_live":
        raise HTTPException(409, "Engine refused to trade: live account detected and ALLOW_LIVE is not enabled.")
    b.desired_state, b.emergency_close_done = "running", False
    add_log(db, "Start requested from dashboard")
    db.commit()
    return _status(db)


@router.post("/bot/stop")
def stop(db: Session = Depends(get_db)):
    b = get_bot(db)
    b.desired_state = "stopped"
    add_log(db, "Stop requested from dashboard")
    db.commit()
    return _status(db)


@router.post("/bot/emergency-stop")
def emergency(body: EmergencyIn | None = None, db: Session = Depends(get_db)):
    b, r = get_bot(db), get_risk(db)
    if body and body.closePositions is not None:
        r.close_on_emergency = body.closePositions
    b.desired_state, b.emergency_close_done = "emergency", False
    add_log(db, f"EMERGENCY STOP requested (close positions: {r.close_on_emergency})", "warn")
    add_notification(db, "emergency", "Emergency stop requested from dashboard")
    db.commit()
    return _status(db)


@router.get("/logs")
def logs(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(BotLog).order_by(BotLog.id.desc()).limit(min(limit, 500))
    return [{"t": iso(l.created_at), "level": l.level, "m": l.message} for l in rows]


@router.get("/notifications")
def notifications(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(Notification).order_by(Notification.id.desc()).limit(min(limit, 500))
    return [{"t": iso(n.created_at), "kind": n.kind, "m": n.message, "sent": n.sent} for n in rows]


@router.get("/state")
def state(db: Session = Depends(get_db)):
    """Everything the dashboard needs in one poll (shape mirrors the frontend simulator)."""
    b = get_bot(db)
    closed = db.query(Trade).filter_by(status="CLOSED").order_by(Trade.id.desc()).limit(200).all()
    opened = db.query(Trade).filter_by(status="OPEN").order_by(Trade.id).all()
    return {**_status(db), "engine": get_engine_status(),
            "bal": b.balance, "equity": b.equity, "peak": b.peak_equity, "dayStartEquity": b.day_start_equity,
            "account": {"login": b.account_login, "type": b.account_type},
            "pos": [ser_trade(t) for t in opened], "trades": [ser_trade(t) for t in closed],
            "risk": ser_risk(get_risk(db)), "tgm": b.telegram_enabled, "ai": b.ai_enabled,
            "strat": {s.name: {"on": s.enabled, "tf": s.timeframes.replace(",", ", ")} for s in db.query(Strategy).order_by(Strategy.id)},
            "on": {p.symbol: p.enabled for p in db.query(TradingPair).order_by(TradingPair.id)},
            "logs": [{"t": iso(l.created_at), "m": l.message} for l in db.query(BotLog).order_by(BotLog.id.desc()).limit(80)],
            "signals": _signals(db)}
