import pandas as pd


def bollinger(s: pd.Series, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    mid, sd = s.rolling(period).mean(), s.rolling(period).std()
    return pd.DataFrame({"mid": mid, "upper": mid + std * sd, "lower": mid - std * sd})
