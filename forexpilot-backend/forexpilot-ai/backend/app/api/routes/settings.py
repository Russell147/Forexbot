from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import TradingPair
from app.schemas import BotSettingsIn, EnabledIn, RiskIn
from app.services.state import RISK_MAP, add_log, get_bot, get_risk, ser_risk

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    bot = get_bot(db)
    return {"telegramEnabled": bot.telegram_enabled, "aiEnabled": bot.ai_enabled, "risk": ser_risk(get_risk(db)),
            "pairs": {p.symbol: p.enabled for p in db.query(TradingPair).order_by(TradingPair.id)}}


@router.put("/settings")
def put_settings(body: BotSettingsIn, db: Session = Depends(get_db)):
    bot = get_bot(db)
    if body.telegramEnabled is not None:
        bot.telegram_enabled = body.telegramEnabled
    if body.aiEnabled is not None:
        bot.ai_enabled = body.aiEnabled
    db.commit()
    return {"telegramEnabled": bot.telegram_enabled, "aiEnabled": bot.ai_enabled}


@router.get("/settings/risk")
def get_risk_settings(db: Session = Depends(get_db)):
    return ser_risk(get_risk(db))


@router.put("/settings/risk")
def put_risk(body: RiskIn, db: Session = Depends(get_db)):
    r = get_risk(db)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(r, RISK_MAP[k], v)
    add_log(db, "Risk settings updated")
    db.commit()
    return ser_risk(r)


@router.put("/settings/pairs/{symbol}")
def set_pair(symbol: str, body: EnabledIn, db: Session = Depends(get_db)):
    p = db.query(TradingPair).filter_by(symbol=symbol.upper()).first()
    if not p:
        raise HTTPException(404, "Unknown pair")
    p.enabled = body.on
    db.commit()
    return {"symbol": p.symbol, "enabled": p.enabled}
