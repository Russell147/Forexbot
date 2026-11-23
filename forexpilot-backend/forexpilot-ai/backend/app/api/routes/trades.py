from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Trade
from app.services.state import ser_trade

router = APIRouter(tags=["trades"])


@router.get("/trades")
def trades(status: str | None = Query(None, pattern="^(OPEN|CLOSED)$"), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    q = db.query(Trade)
    if status:
        q = q.filter(Trade.status == status)
    return [ser_trade(t) for t in q.order_by(Trade.id.desc()).limit(limit)]


@router.get("/positions")
def positions(db: Session = Depends(get_db)):
    return [ser_trade(t) for t in db.query(Trade).filter_by(status="OPEN").order_by(Trade.id)]
