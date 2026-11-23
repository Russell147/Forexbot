from datetime import datetime, timezone

import MetaTrader5 as mt5

from ai.signal_validator import ai_review
from app.models import Trade, TradingSignal
from config import settings
from execution.execution_validator import validate_order
from monitoring.health_monitor import add_log, notify
from mt5.market_data import bsym, ensure_symbol, spread_pips
from mt5.order_executor import send_market_order
from risk.position_sizing import lot_size
from risk.risk_manager import check_new_trade


def _record(db, sym, strat, tf, sig, status, reason, ai_note=""):
    db.add(TradingSignal(symbol=sym, strategy=strat, timeframe=tf, direction=sig.direction, status=status, reason=reason[:500], ai_note=ai_note))


def try_trade(db, bot, risk, sym, strat, tf, sig, df, open_positions, symbol_open) -> bool:
    info = ensure_symbol(sym)
    tick = mt5.symbol_info_tick(bsym(sym))
    sp = spread_pips(sym)
    if not info or not tick or sp is None:
        _record(db, sym, strat, tf, sig, "REJECTED", "no market data")
        return False
    buy = sig.direction == "BUY"
    entry = tick.ask if buy else tick.bid
    sl = round(entry - sig.sl_dist if buy else entry + sig.sl_dist, info.digits)
    tp = round(entry + sig.tp_dist if buy else entry - sig.tp_dist, info.digits)
    rr = abs(tp - entry) / abs(entry - sl) if entry != sl else 0
    today = datetime.now(timezone.utc).date()
    trades_today = sum(1 for t in db.query(Trade).all()
                       if t.opened_at is not None and t.opened_at.date() == today)
    loss_cap = max(1, int(getattr(risk, "max_consecutive_losses", 3) or 3))
    closed = db.query(Trade).filter_by(status="CLOSED").order_by(Trade.closed_at.desc()).limit(loss_cap).all()
    consecutive_losses = 0
    for t in closed:
        if (t.profit or 0) <= 0:
            consecutive_losses += 1
        else:
            break
    why = check_new_trade(risk, open_count=open_positions, symbol_open=symbol_open, spread_pips=sp, rr=rr,
                          equity=bot.equity, day_start=bot.day_start_equity, peak=bot.peak_equity,
                          trades_today=trades_today, consecutive_losses=consecutive_losses)
    vol = None
    if not why:
        vol, msg = lot_size(bot.equity, risk.risk_per_trade, entry, sl, info)
        why = None if vol else msg
    if not why:
        why = validate_order(info, sig.direction, vol, entry, sl, tp)
    ai_note = ""
    if not why and bot.ai_enabled and settings.GEMINI_API_KEY:
        ok, ai_note = ai_review(sym, tf, strat, sig, df)
        why = None if ok else ai_note
    if why:
        _record(db, sym, strat, tf, sig, "REJECTED", why, ai_note)
        add_log(db, f"WAIT {sym} {tf} {sig.direction}: {why}")
        return False
    ok, msg, ticket, fill = send_market_order(sym, sig.direction, vol, sl, tp, f"FP {strat}")
    if not ok:
        _record(db, sym, strat, tf, sig, "REJECTED", msg, ai_note)
        add_log(db, f"Order rejected {sym}: {msg}", "error")
        return False
    db.add(Trade(ticket=ticket, symbol=sym, type=sig.direction, volume=vol, entry_price=fill or entry, stop_loss=sl, take_profit=tp, strategy=strat))
    _record(db, sym, strat, tf, sig, "EXECUTED", sig.reason, ai_note)
    text = f"Opened {sig.direction} {sym} {vol} lot @ {fill or entry} SL {sl} TP {tp} [{strat} {tf}]"
    add_log(db, text)
    notify(db, bot, "trade_opened", text)
    return True
