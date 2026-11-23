from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import TradingAccount, User
from app.schemas import AccountIn
from app.services.state import get_bot

router = APIRouter(tags=["accounts"])


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    bot = get_bot(db)
    rows = db.query(TradingAccount).all()
    return {"live": {"login": bot.account_login, "type": bot.account_type, "balance": bot.balance, "equity": bot.equity,
                     "connected": bot.mt5_connected},
            "accounts": [{"id": a.id, "login": a.login, "server": a.server, "broker": a.broker, "type": a.account_type,
                          "currency": a.currency, "active": a.is_active} for a in rows]}


@router.post("/accounts", status_code=201)
def add_account(body: AccountIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = TradingAccount(user_id=user.id, **body.model_dump())
    db.add(a)
    db.commit()
    return {"id": a.id, "note": "Metadata saved. Set MT5_LOGIN / MT5_PASSWORD / MT5_SERVER in the engine's .env on the VPS."}
