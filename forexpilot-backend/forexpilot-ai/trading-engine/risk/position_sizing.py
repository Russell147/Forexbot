import math


def lot_size(equity: float, risk_pct: float, entry: float, sl: float, info) -> tuple[float | None, str]:
    """Volume so that a stop-out loses ~risk_pct of equity. Returns (None, reason) if it cannot be done safely.
    `info` is an MT5 symbol_info (needs trade_tick_size/value, volume_min/max/step)."""
    risk_money = equity * risk_pct / 100
    dist = abs(entry - sl)
    if dist <= 0 or info.trade_tick_size <= 0 or info.trade_tick_value <= 0:
        return None, "invalid stop distance or symbol tick data"
    loss_per_lot = dist / info.trade_tick_size * info.trade_tick_value
    steps = math.floor(risk_money / loss_per_lot / info.volume_step + 1e-9)
    vol = round(steps * info.volume_step, 8)
    if vol < info.volume_min:
        return None, (f"minimum lot {info.volume_min} would risk ${info.volume_min * loss_per_lot:.2f}, "
                      f"above the allowed ${risk_money:.2f} ({risk_pct}% of equity)")
    return min(vol, info.volume_max), f"risk ${vol * loss_per_lot:.2f}"
