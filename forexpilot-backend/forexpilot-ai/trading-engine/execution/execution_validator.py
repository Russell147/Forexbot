def validate_order(info, side: str, volume: float, entry: float, sl: float, tp: float) -> str | None:
    """Pre-flight checks. Returns a rejection reason or None."""
    if info is None:
        return "symbol not available"
    if getattr(info, "trade_mode", 4) == 0:
        return "trading disabled for symbol"
    if not sl or not tp:
        return "stop-loss and take-profit are mandatory"
    if side == "BUY" and not (sl < entry < tp):
        return "invalid SL/TP for BUY"
    if side == "SELL" and not (tp < entry < sl):
        return "invalid SL/TP for SELL"
    min_dist = info.trade_stops_level * info.point
    if abs(entry - sl) < min_dist or abs(tp - entry) < min_dist:
        return "SL/TP closer than broker's minimum stop distance"
    if not (info.volume_min <= volume <= info.volume_max):
        return "volume outside broker limits"
    return None
