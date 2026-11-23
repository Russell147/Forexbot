from sqlalchemy.orm import Session

from app.models import BotSettings, RiskSettings, Strategy, TradingPair

PAIRS = {"EURUSD": "Euro / US Dollar", "GBPUSD": "British Pound / US Dollar", "USDJPY": "US Dollar / Japanese Yen",
         "USDCHF": "US Dollar / Swiss Franc", "AUDUSD": "Australian Dollar / US Dollar",
         "USDCAD": "US Dollar / Canadian Dollar", "NZDUSD": "New Zealand Dollar / US Dollar"}
STRATS = {"Scalping": ("M1,M5,M15", True), "Day Trading": ("M15,M30,H1", True), "Swing Trading": ("H4,D1", False)}


def seed(db: Session) -> None:
    for sym, desc in PAIRS.items():
        if not db.query(TradingPair).filter_by(symbol=sym).first():
            db.add(TradingPair(symbol=sym, description=desc))
    for name, (tfs, on) in STRATS.items():
        if not db.query(Strategy).filter_by(name=name).first():
            db.add(Strategy(name=name, timeframes=tfs, enabled=on))
    if not db.get(RiskSettings, 1):
        db.add(RiskSettings(id=1))
    if not db.get(BotSettings, 1):
        db.add(BotSettings(id=1))
    db.commit()
