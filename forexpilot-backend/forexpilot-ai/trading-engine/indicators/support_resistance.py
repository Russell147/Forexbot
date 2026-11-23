"""Simple recent swing support/resistance levels."""
import pandas as pd


def support_resistance(df: pd.DataFrame, lookback: int = 100, levels: int = 3) -> tuple[float, float]:
    """Return (support, resistance) from recent pivots around the last close."""
    if df is None or len(df) < 5:
        return 0.0, 0.0
    d = df.tail(max(lookback, 10))
    price = float(d["close"].iat[-1])
    lows = sorted(float(x) for x in d["low"].nsmallest(levels))
    highs = sorted(float(x) for x in d["high"].nlargest(levels))
    support = max((x for x in lows if x < price), default=lows[0])
    resistance = min((x for x in highs if x > price), default=highs[-1])
    return support, resistance
