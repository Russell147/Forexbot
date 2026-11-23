from strategies.base_strategy import EmaRsiStrategy


class DayTradingStrategy(EmaRsiStrategy):
    timeframes = ["M15", "M30", "H1"]
    params = {**EmaRsiStrategy.params, "fast": 20, "slow": 50, "atr_sl_mult": 1.5}
