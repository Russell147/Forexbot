"""EMA-cross + RSI-confirmation baseline. An UNPROVEN test strategy: validate with backtests and demo trading."""
from dataclasses import dataclass

import pandas as pd

from indicators.atr import atr
from indicators.moving_average import ema
from indicators.rsi import rsi


@dataclass
class Signal:
    direction: str | None  # "BUY" | "SELL" | None (WAIT)
    reason: str = ""
    sl_dist: float = 0.0   # price distance, applied to the real fill price
    tp_dist: float = 0.0
    atr: float = 0.0
    rsi: float = 0.0


class EmaRsiStrategy:
    name = "EMA_RSI"
    timeframes: list[str] = ["M15"]
    params = dict(fast=20, slow=50, rsi_period=14, rsi_buy=(50, 70), rsi_sell=(30, 50), atr_period=14, atr_sl_mult=1.5, rr=2.0)

    def __init__(self, **overrides):
        self.p = {**self.params, **overrides}

    @property
    def warmup(self) -> int:
        return max(self.p["slow"], self.p["rsi_period"], self.p["atr_period"]) * 3

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        d, p = df.copy(), self.p
        d["ef"], d["es"] = ema(d["close"], p["fast"]), ema(d["close"], p["slow"])
        d["rsi"], d["atr"] = rsi(d["close"], p["rsi_period"]), atr(d, p["atr_period"])
        return d

    def signal_at(self, d: pd.DataFrame, i: int) -> Signal:
        """Signal using only data up to and including candle i (which must be a CLOSED candle)."""
        p = self.p
        if i < self.warmup or pd.isna(d["atr"].iat[i]) or d["atr"].iat[i] <= 0:
            return Signal(None, "warming up")
        up = d["ef"].iat[i - 1] <= d["es"].iat[i - 1] and d["ef"].iat[i] > d["es"].iat[i]
        dn = d["ef"].iat[i - 1] >= d["es"].iat[i - 1] and d["ef"].iat[i] < d["es"].iat[i]
        r, a = float(d["rsi"].iat[i]), float(d["atr"].iat[i])
        sl = a * p["atr_sl_mult"]
        mk = lambda dirn, why: Signal(dirn, why, sl, sl * p["rr"], a, r)
        if up and p["rsi_buy"][0] <= r <= p["rsi_buy"][1]:
            return mk("BUY", f"EMA{p['fast']} crossed above EMA{p['slow']}, RSI {r:.0f}")
        if dn and p["rsi_sell"][0] <= r <= p["rsi_sell"][1]:
            return mk("SELL", f"EMA{p['fast']} crossed below EMA{p['slow']}, RSI {r:.0f}")
        return Signal(None, "no confirmed cross")

    def evaluate(self, closed_df: pd.DataFrame) -> Signal:
        d = self.compute(closed_df)
        return self.signal_at(d, len(d) - 1)
