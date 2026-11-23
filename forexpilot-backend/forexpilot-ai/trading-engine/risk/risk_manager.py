from datetime import datetime, timezone

from risk.drawdown_control import daily_loss_pct, drawdown_pct

SESSIONS = {"All sessions": (0, 24), "London": (7, 16), "New York": (12, 21), "London + New York": (7, 21)}  # UTC hours


def in_session(name: str, now: datetime | None = None) -> bool:
    lo, hi = SESSIONS.get(name, (0, 24))
    return lo <= (now or datetime.now(timezone.utc)).hour < hi


def limit_breach(risk, equity: float, day_start: float, peak: float) -> str | None:
    if daily_loss_pct(day_start, equity) >= risk.max_daily_loss:
        return f"Daily loss limit reached ({risk.max_daily_loss}%)"
    if drawdown_pct(peak, equity) >= risk.max_drawdown:
        return f"Max drawdown reached ({risk.max_drawdown}%)"
    return None


def check_new_trade(risk, *, open_count: int, symbol_open: bool, spread_pips: float, rr: float,
                    equity: float, day_start: float, peak: float, now: datetime | None = None) -> str | None:
    """Return a rejection reason, or None if the trade may proceed."""
    if (b := limit_breach(risk, equity, day_start, peak)):
        return b
    if open_count >= risk.max_open_positions:
        return "max open positions reached"
    if symbol_open:
        return "duplicate: position already open on this symbol"
    if spread_pips > risk.max_spread_pips:
        return f"spread {spread_pips:.1f}p above limit {risk.max_spread_pips}p"
    if rr + 1e-9 < risk.min_risk_reward:
        return f"risk/reward {rr:.2f} below minimum {risk.min_risk_reward}"
    if not in_session(risk.session, now):
        return f"outside session ({risk.session})"
    return None
