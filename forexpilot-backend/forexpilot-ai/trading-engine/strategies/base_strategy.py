"""Rule-based EMA(20/50) + RSI(14) strategy with confluence confirmation.

UNPROVEN test strategy: validate with backtests and demo trading before trusting
it. MACD, candlestick patterns, trend classification and support/resistance are
used only to CONFIRM or veto an EMA-cross trigger and to populate the dashboard's
analysis panel. They never create a trade by themselves.
"""
from dataclasses import dataclass

import pandas as pd

from indicators.atr import atr
from indicators.candlestick import candlestick_signal
from indicators.macd import macd
from indicators.moving_average import ema
from indicators.rsi import rsi
from indicators.support_resistance import support_resistance
from indicators.trend import detect_trend


@dataclass
class Signal:
    direction: str | None  # "BUY" | "SELL" | None (HOLD / no trade)
    reason: str = ""
    sl_dist: float = 0.0   # price distance, applied to the real fill price
    tp_dist: float = 0.0
    atr: float = 0.0
    rsi: float = 0.0
    # Analysis snapshot (latest CLOSED candle) for the dashboard
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    trend: str = "RANGE"
    candle: str = "no pattern"
    support: float = 0.0
    resistance: float = 0.0
    price: float = 0.0

    @property
    def label(self) -> str:
        return self.direction or "HOLD"

    def analysis(self) -> dict:
        return {
            "signal": self.label,
            "reason": self.reason,
            "emaFast": self.ema_fast,
            "emaSlow": self.ema_slow,
            "ema20": self.ema20,
            "ema50": self.ema50,
            "rsi": self.rsi,
            "macd": self.macd,
            "macdSignal": self.macd_signal,
            "macdHist": self.macd_hist,
            "trend": self.trend,
            "candle": self.candle,
            "support": self.support,
            "resistance": self.resistance,
            "atr": self.atr,
            "price": self.price,
        }


class EmaRsiStrategy:
    name = "EMA_RSI"
    timeframes: list[str] = ["M15"]
    params = dict(fast=20, slow=50, rsi_period=14, rsi_buy=(50, 70), rsi_sell=(30, 50),
                  atr_period=14, atr_sl_mult=1.5, rr=2.0, sr_lookback=100, sr_levels=3)

    def __init__(self, **overrides):
        self.p = {**self.params, **overrides}

    @property
    def warmup(self) -> int:
        return max(self.p["slow"], self.p["rsi_period"], self.p["atr_period"], 50) * 3

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        d, p = df.copy(), self.p
        d["ef"], d["es"] = ema(d["close"], p["fast"]), ema(d["close"], p["slow"])
        d["ema20"], d["ema50"] = ema(d["close"], 20), ema(d["close"], 50)
        d["rsi"] = rsi(d["close"], p["rsi_period"])
        d["atr"] = atr(d, p["atr_period"])
        m = macd(d["close"])
        d["macd"], d["macd_signal"], d["macd_hist"] = m["macd"], m["signal"], m["hist"]
        return d

    @staticmethod
    def _confirms(side: str, macd_hist: float, trend: str, candle_bias: str) -> bool:
        """Require momentum/trend alignment; veto only on a clear contradiction."""
        if side == "BUY":
            if macd_hist <= 0 or trend == "BEARISH" or candle_bias == "BEARISH":
                return False
        else:
            if macd_hist >= 0 or trend == "BULLISH" or candle_bias == "BULLISH":
                return False
        return True

    def signal_at(self, d: pd.DataFrame, i: int) -> Signal:
        """Signal using only data up to and including candle i (a CLOSED candle)."""
        p = self.p
        if i < self.warmup or pd.isna(d["atr"].iat[i]) or d["atr"].iat[i] <= 0:
            return Signal(None, "warming up")
        ef, es = float(d["ef"].iat[i]), float(d["es"].iat[i])
        r, a, mh = float(d["rsi"].iat[i]), float(d["atr"].iat[i]), float(d["macd_hist"].iat[i])
        window = d.iloc[: i + 1]
        trend = detect_trend(float(d["ema20"].iat[i]), float(d["ema50"].iat[i]), mh, window["close"])
        candle = candlestick_signal(window)
        support, resistance = support_resistance(window, int(p["sr_lookback"]), int(p["sr_levels"]))
        base = dict(ema_fast=ef, ema_slow=es, ema20=float(d["ema20"].iat[i]), ema50=float(d["ema50"].iat[i]),
                    rsi=r, atr=a, macd=float(d["macd"].iat[i]), macd_signal=float(d["macd_signal"].iat[i]),
                    macd_hist=mh, trend=trend, candle=candle.reason, support=support, resistance=resistance,
                    price=float(d["close"].iat[i]))
        up = d["ef"].iat[i - 1] <= d["es"].iat[i - 1] and ef > es
        dn = d["ef"].iat[i - 1] >= d["es"].iat[i - 1] and ef < es
        sl = a * p["atr_sl_mult"]
        tp = sl * p["rr"]
        if up and p["rsi_buy"][0] <= r <= p["rsi_buy"][1]:
            if self._confirms("BUY", mh, trend, candle.bias):
                reason = f"EMA cross up, RSI {r:.0f}, {trend}, {candle.reason}, MACD hist {mh:+.5f}"
                return Signal("BUY", reason, sl, tp, **base)
            return Signal(None, f"BUY cross unconfirmed ({trend}, {candle.reason}, MACD hist {mh:+.5f})", **base)
        if dn and p["rsi_sell"][0] <= r <= p["rsi_sell"][1]:
            if self._confirms("SELL", mh, trend, candle.bias):
                reason = f"EMA cross down, RSI {r:.0f}, {trend}, {candle.reason}, MACD hist {mh:+.5f}"
                return Signal("SELL", reason, sl, tp, **base)
            return Signal(None, f"SELL cross unconfirmed ({trend}, {candle.reason}, MACD hist {mh:+.5f})", **base)
        return Signal(None, f"no confirmed cross ({trend}, RSI {r:.0f})", **base)

    def evaluate(self, closed_df: pd.DataFrame) -> Signal:
        d = self.compute(closed_df)
        return self.signal_at(d, len(d) - 1)
