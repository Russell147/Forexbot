from datetime import datetime, timezone

import MetaTrader5 as mt5

from app.models import Performance, Trade
from mt5.market_data import base_symbol
from mt5.position_manager import open_positions
from monitoring.health_monitor import add_log, notify

_REASON = {mt5.DEAL_REASON_SL: "Stop-loss", mt5.DEAL_REASON_TP: "Take-profit", mt5.DEAL_REASON_SO: "Stop-out"}


def sync_positions(db, bot, strat_by_ticket_default="recovered") -> None:
    """Reconcile DB trades with MT5: update floating P/L, record closes, adopt unknown positions."""
    live = {p.ticket: p for p in open_positions()}
    for t in db.query(Trade).filter_by(status="OPEN").all():
        p = live.get(t.ticket)
        if p:
            t.profit = p.profit + p.swap
            t.stop_loss, t.take_profit = p.sl, p.tp
            continue
        deals = mt5.history_deals_get(position=t.ticket) or []
        outs = [d for d in deals if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY)]
        t.status, t.closed_at = "CLOSED", datetime.now(timezone.utc)
        if outs:
            t.exit_price = outs[-1].price
            t.profit = sum(d.profit + d.commission + d.swap + getattr(d, "fee", 0) for d in deals)
            t.close_reason = _REASON.get(outs[-1].reason, "Closed")
        else:
            t.close_reason = "Closed (details pending)"
        msg = f"Trade closed: {t.type} {t.symbol} {t.profit:+.2f} ({t.close_reason})"
        add_log(db, msg)
        notify(db, bot, "trade_closed", msg)
    known = {t.ticket for t in db.query(Trade.ticket).all()}
    for tk, p in live.items():
        if tk not in known:
            db.add(Trade(ticket=tk, symbol=base_symbol(p.symbol), type="BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL", volume=p.volume,
                         entry_price=p.price_open, stop_loss=p.sl, take_profit=p.tp, profit=p.profit + p.swap, strategy="recovered"))
            add_log(db, f"Adopted untracked position {tk} on {p.symbol}", "warn")


def snapshot(db, balance: float, equity: float) -> None:
    db.add(Performance(balance=balance, equity=equity))
