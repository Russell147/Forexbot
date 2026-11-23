import pandas as pd


def rsi(s: pd.Series, period: int = 14) -> pd.Series:
    d = s.diff()
    up, dn = d.clip(lower=0), -d.clip(upper=0)
    rs = up.ewm(alpha=1 / period, adjust=False).mean() / dn.ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + rs)
