from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Strategy
from app.schemas import EnabledIn
from app.services.state import add_log

router = APIRouter(tags=["strategies"])


def _s(s: Strategy) -> dict:
    return {"name": s.name, "on": s.enabled, "tf": s.timeframes.replace(",", ", "), "params": s.params}


@router.get("/strategies")
def list_strategies(db: Session = Depends(get_db)):
    return [_s(s) for s in db.query(Strategy).order_by(Strategy.id)]


@router.put("/strategies/{name}")
def set_strategy(name: str, body: EnabledIn, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter_by(name=name).first()
    if not s:
        raise HTTPException(404, "Unknown strategy")
    s.enabled = body.on
    add_log(db, f"Strategy {name} {'enabled' if body.on else 'disabled'}")
    db.commit()
    return _s(s)
