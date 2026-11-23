from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Performance, Trade
from app.services.state import iso, trade_stats

router = APIRouter(tags=["analytics"])


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    closed = db.query(Trade).filter_by(status="CLOSED").all()
    by_pair: dict[str, float] = {}
    for t in closed:
        by_pair[t.symbol] = by_pair.get(t.symbol, 0.0) + t.profit
    curve = db.query(Performance).order_by(Performance.id.desc()).limit(500).all()[::-1]
    return {**trade_stats(closed), "byPair": by_pair,
            "equityCurve": [{"t": iso(p.ts), "balance": p.balance, "equity": p.equity} for p in curve]}
