from strategies.base_strategy import EmaRsiStrategy


class ScalpingStrategy(EmaRsiStrategy):
    timeframes = ["M1", "M5", "M15"]
    params = {**EmaRsiStrategy.params, "fast": 9, "slow": 21, "atr_sl_mult": 1.2}
