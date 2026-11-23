def daily_loss_pct(day_start_equity: float, equity: float) -> float:
    return max(0.0, (day_start_equity - equity) / day_start_equity * 100) if day_start_equity > 0 else 0.0


def drawdown_pct(peak_equity: float, equity: float) -> float:
    return max(0.0, (peak_equity - equity) / peak_equity * 100) if peak_equity > 0 else 0.0
