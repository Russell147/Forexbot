import math


def lot_size(equity: float, risk_pct: float, entry: float, sl: float, info,
             *, max_lot: float = 0.0, fixed_lot: float = 0.0) -> tuple[float | None, str]:
    """Volume for one trade.

    Default mode: size so a stop-out loses ~risk_pct of equity.
    If ``fixed_lot`` > 0 that volume is used instead (risk sizing is ignored).
    ``max_lot`` > 0 caps the result in either mode.

    The result is always snapped to the broker's volume step and kept within
    its min/max. Returns (None, reason) when nothing safe can be traded.
    """
    if fixed_lot > 0:
        vol = float(fixed_lot)
        detail = f"fixed lot {vol:g}"
    else:
        risk_money = equity * risk_pct / 100
        dist = abs(entry - sl)
        if dist <= 0 or info.trade_tick_size <= 0 or info.trade_tick_value <= 0:
            return None, "invalid stop distance or symbol tick data"
        loss_per_lot = dist / info.trade_tick_size * info.trade_tick_value
        steps = math.floor(risk_money / loss_per_lot / info.volume_step + 1e-9)
        vol = round(steps * info.volume_step, 8)
        detail = f"risk ${vol * loss_per_lot:.2f}"
        if vol < info.volume_min:
            return None, (f"minimum lot {info.volume_min} would risk ${info.volume_min * loss_per_lot:.2f}, "
                          f"above the allowed ${risk_money:.2f} ({risk_pct}% of equity)")

    if max_lot > 0 and vol > max_lot:
        vol = float(max_lot)
        detail += f", capped to {max_lot:g}"

    if info.volume_step > 0:
        vol = round(math.floor(vol / info.volume_step + 1e-9) * info.volume_step, 8)
    if vol < info.volume_min:
        return None, f"lot {vol:g} is below broker minimum {info.volume_min:g} (cap {max_lot:g})"
    vol = min(vol, info.volume_max)
    return vol, detail
