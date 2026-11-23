"""Trend classification from EMA 20/50, MACD histogram and recent price slope."""
import pandas as pd

BULLISH = "BULLISH"
BEARISH = "BEARISH"
RANGE = "RANGE"


def detect_trend(ema_fast: float, ema_slow: float, macd_hist: float, closes: pd.Series, lookback: int = 5) -> str:
    values = (ema_fast, ema_slow, macd_hist)
    if any(pd.isna(v) for v in values) or closes is None or len(closes) < lookback:
        return RANGE
    slope = float(closes.iat[-1]) - float(closes.iat[-lookback])
    if ema_fast > ema_slow and macd_hist > 0 and slope > 0:
        return BULLISH
    if ema_fast < ema_slow and macd_hist < 0 and slope < 0:
        return BEARISH
    return RANGE
