"""Apply smarter exit rules to existing MT5 positions (demo only)."""
import logging
from datetime import datetime, timezone

import MetaTrader5 as mt5

from app.models import Trade
from monitoring.health_monitor import add_log
from mt5 import market_data as md
from mt5.position_manager import close_position, open_positions, set_stop_loss
from risk.exit_rules import BREAK_EVEN, PARTIAL_TP, TIME_EXIT, decide_exit

log = logging.getLogger("engine.exits")


def manage_exits(db, bot, risk) -> None:
    """Break-even, partial take-profit and time exits — one action per position per poll."""
    be_r = float(getattr(risk, "break_even_after_r", 0) or 0)
    tp_r = float(getattr(risk, "partial_tp_r", 0) or 0)
    tp_pct = float(getattr(risk, "partial_tp_pct", 0) or 0)
    hold_h = float(getattr(risk, "max_hold_hours", 0) or 0)
    if not (be_r or (tp_r and tp_pct) or hold_h):
        return

    for p in open_positions():
        t = db.query(Trade).filter_by(ticket=p.ticket, status="OPEN").first()
        if t is None:
            continue
        tick, info = mt5.symbol_info_tick(p.symbol), mt5.symbol_info(p.symbol)
        if not tick or not info:
            continue
        buy = p.type == mt5.POSITION_TYPE_BUY
        opened_ms = getattr(p, "time_msc", 0) or float(getattr(p, "time", 0)) * 1000
        opened_hours = max(0.0, (datetime.now(timezone.utc) - datetime.fromtimestamp(opened_ms / 1000, timezone.utc)).total_seconds() / 3600)

        action = decide_exit(
            buy=buy, entry=float(p.price_open), stop=float(p.sl or 0), bid=float(tick.bid), ask=float(tick.ask),
            opened_hours=opened_hours, initial_stop=float(t.initial_stop or p.sl or 0),
            break_even_after_r=be_r, partial_tp_r=tp_r, partial_tp_pct=tp_pct,
            partial_done=bool(getattr(t, "partial_done", False)), max_hold_hours=hold_h,
        )
        if action.action == TIME_EXIT:
            if close_position(p, "ForexPilot time exit"):
                add_log(db, f"Closed {t.symbol} on time exit ({opened_hours:.1f}h)")
        elif action.action == PARTIAL_TP:
            vol = float(p.volume) * action.close_fraction
            if close_position(p, "ForexPilot partial TP", volume=vol):
                t.partial_done = True
                add_log(db, f"Closed {action.close_fraction:.0%} of {t.symbol} at {tp_r}R")
        elif action.action == BREAK_EVEN and action.new_sl is not None:
            # Respect the broker's minimum stop distance with a tiny profit buffer.
            buffer = float(info.trade_stops_level or 0) * float(info.point or 0)
            new_sl = action.new_sl + buffer if buy else action.new_sl - buffer
            if set_stop_loss(p, new_sl, "break-even"):
                add_log(db, f"Moved {t.symbol} SL to break-even ({be_r}R)")
        if action.action != "NONE":
            db.commit()
