"""Load OHLC data for backtests: from CSV, from MT5 (Windows), or a synthetic series for smoke tests only."""
import numpy as np
import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]
    df["time"] = pd.to_datetime(df["time"])
    return df[["time", "open", "high", "low", "close"]].sort_values("time").reset_index(drop=True)


def download_mt5(symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
    import MetaTrader5 as mt5

    tf = getattr(mt5, f"TIMEFRAME_{timeframe}")
    if not mt5.initialize():
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    rates = mt5.copy_rates_range(symbol, tf, pd.Timestamp(start).to_pydatetime(), pd.Timestamp(end).to_pydatetime())
    mt5.shutdown()
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df[["time", "open", "high", "low", "close"]]


def synthetic(n: int = 5000, seed: int = 1, start: float = 1.1, vol: float = 0.0004) -> pd.DataFrame:
    """Random walk. ONLY for testing the pipeline: results on it say nothing about real profitability."""
    rng = np.random.default_rng(seed)
    close = start + np.cumsum(rng.normal(0, vol, n))
    open_ = np.r_[start, close[:-1]]
    spread = np.abs(rng.normal(0, vol / 2, n))
    return pd.DataFrame({"time": pd.date_range("2024-01-01", periods=n, freq="15min"), "open": open_,
                         "high": np.maximum(open_, close) + spread, "low": np.minimum(open_, close) - spread, "close": close})
