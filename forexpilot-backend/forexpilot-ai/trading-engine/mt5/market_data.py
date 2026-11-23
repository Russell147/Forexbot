import MetaTrader5 as mt5
import pandas as pd

from config import settings

TF = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
      "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4, "D1": mt5.TIMEFRAME_D1}


def bsym(symbol: str) -> str:
    return symbol + settings.SYMBOL_SUFFIX


def base_symbol(broker_symbol: str) -> str:
    s = settings.SYMBOL_SUFFIX
    return broker_symbol[: -len(s)] if s and broker_symbol.endswith(s) else broker_symbol


def ensure_symbol(symbol: str):
    mt5.symbol_select(bsym(symbol), True)
    return mt5.symbol_info(bsym(symbol))


def pip_size(info) -> float:
    return info.point * 10 if info.digits in (3, 5) else info.point


def spread_pips(symbol: str) -> float | None:
    t, info = mt5.symbol_info_tick(bsym(symbol)), mt5.symbol_info(bsym(symbol))
    return None if not t or not info else (t.ask - t.bid) / pip_size(info)


def get_rates(symbol: str, tf: str, count: int = 300) -> pd.DataFrame | None:
    r = mt5.copy_rates_from_pos(bsym(symbol), TF[tf], 0, count)
    if r is None or len(r) == 0:
        return None
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df
