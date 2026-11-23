import MetaTrader5 as mt5

from config import settings
from mt5.order_executor import _filling


def open_positions() -> list:
    return [p for p in (mt5.positions_get() or []) if p.magic == settings.MAGIC]


def close_position(p, comment: str = "ForexPilot close") -> bool:
    tick, info = mt5.symbol_info_tick(p.symbol), mt5.symbol_info(p.symbol)
    if not tick or not info:
        return False
    buy = p.type == mt5.POSITION_TYPE_BUY
    res = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
                          "type": mt5.ORDER_TYPE_SELL if buy else mt5.ORDER_TYPE_BUY, "price": tick.bid if buy else tick.ask,
                          "deviation": settings.DEVIATION, "magic": settings.MAGIC, "comment": comment[:31],
                          "type_time": mt5.ORDER_TIME_GTC, "type_filling": _filling(info)})
    return bool(res and res.retcode == mt5.TRADE_RETCODE_DONE)


def apply_trailing(p, atr_value: float, mult: float) -> bool:
    """Move SL toward price by mult*ATR, never loosening it and respecting the broker's stop level."""
    tick, info = mt5.symbol_info_tick(p.symbol), mt5.symbol_info(p.symbol)
    if not tick or not info or atr_value <= 0:
        return False
    buy = p.type == mt5.POSITION_TYPE_BUY
    new = round((tick.bid - mult * atr_value) if buy else (tick.ask + mult * atr_value), info.digits)
    better = new > p.sl if buy else (p.sl == 0 or new < p.sl)
    far = (tick.bid - new) if buy else (new - tick.ask)
    if not better or far < info.trade_stops_level * info.point:
        return False
    res = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": p.symbol, "position": p.ticket, "sl": new, "tp": p.tp})
    return bool(res and res.retcode == mt5.TRADE_RETCODE_DONE)
