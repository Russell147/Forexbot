from strategies.base_strategy import EmaRsiStrategy


class SwingTradingStrategy(EmaRsiStrategy):
    timeframes = ["H4", "D1"]
    params = {**EmaRsiStrategy.params, "fast": 20, "slow": 50, "atr_sl_mult": 2.0}
