import MetaTrader5 as mt5

from config import settings
from mt5.market_data import bsym


def _filling(info) -> int:
    fm = info.filling_mode
    if fm & 2:
        return mt5.ORDER_FILLING_IOC
    if fm & 1:
        return mt5.ORDER_FILLING_FOK
    return mt5.ORDER_FILLING_RETURN


def send_market_order(symbol: str, side: str, volume: float, sl: float, tp: float, comment: str = "ForexPilot"):
    """Returns (ok, message, position_ticket, fill_price). Dry-checks the order with order_check first."""
    s, info, tick = bsym(symbol), mt5.symbol_info(bsym(symbol)), mt5.symbol_info_tick(bsym(symbol))
    if not info or not tick:
        return False, "no symbol/tick data", None, None
    buy = side == "BUY"
    req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": s, "volume": volume, "type": mt5.ORDER_TYPE_BUY if buy else mt5.ORDER_TYPE_SELL,
           "price": tick.ask if buy else tick.bid, "sl": sl, "tp": tp, "deviation": settings.DEVIATION, "magic": settings.MAGIC,
           "comment": comment[:31], "type_time": mt5.ORDER_TIME_GTC, "type_filling": _filling(info)}
    chk = mt5.order_check(req)
    if chk is None or chk.retcode != 0:
        return False, f"order_check failed: {getattr(chk, 'comment', mt5.last_error())}", None, None
    res = mt5.order_send(req)
    if res is None or res.retcode != mt5.TRADE_RETCODE_DONE:
        return False, f"order_send failed: {getattr(res, 'comment', mt5.last_error())}", None, None
    ps = [p for p in (mt5.positions_get(symbol=s) or []) if p.magic == settings.MAGIC]
    ticket = max(ps, key=lambda p: p.time_msc).ticket if ps else res.order
    return True, "filled", ticket, res.price
