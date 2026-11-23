"""Candlestick confirmation for the latest CLOSED bar.

These are deliberately simple, non-predictive patterns used only to confirm or
veto a rule-based EMA/RSI signal. They never create a trade on their own.
"""
from dataclasses import dataclass

import pandas as pd

BULLISH = "BULLISH"
BEARISH = "BEARISH"
NEUTRAL = "NEUTRAL"


@dataclass
class CandleSignal:
    bias: str = NEUTRAL
    reason: str = "no pattern"


def candlestick_signal(df: pd.DataFrame) -> CandleSignal:
    if df is None or len(df) < 3:
        return CandleSignal()

    cur, prev = df.iloc[-1], df.iloc[-2]
    o, h, l, c = float(cur["open"]), float(cur["high"]), float(cur["low"]), float(cur["close"])
    po, pc = float(prev["open"]), float(prev["close"])
    body, rng = abs(c - o), h - l
    if rng <= 0:
        return CandleSignal()

    prev_body = abs(pc - po)

    # Engulfing: current candle fully covers the previous opposite-coloured body.
    if c > o and pc < po and c >= po and o <= pc and body > prev_body:
        return CandleSignal(BULLISH, "bullish engulfing")
    if c < o and pc > po and o >= pc and c <= po and body > prev_body:
        return CandleSignal(BEARISH, "bearish engulfing")

    lower, upper = min(o, c) - l, h - max(o, c)
    if body > 0 and body / rng >= 0.1:
        if lower >= 2 * body and upper <= 0.6 * body:
            return CandleSignal(BULLISH, "hammer")
        if upper >= 2 * body and lower <= 0.6 * body:
            return CandleSignal(BEARISH, "shooting star")

    if body / rng <= 0.1:
        return CandleSignal(NEUTRAL, "doji")
    return CandleSignal(NEUTRAL, "no pattern")
