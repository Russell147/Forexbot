"""Pure exit-decision logic for open positions. No MT5 calls, fully testable.

The engine calls :func:`decide_exit` once per poll and the result is applied by
``execution.exit_manager``. Only one action is taken per position per poll.
"""
from dataclasses import dataclass

BREAK_EVEN = "BREAK_EVEN"
PARTIAL_TP = "PARTIAL_TP"
TIME_EXIT = "TIME_EXIT"
NONE = "NONE"


@dataclass
class ExitAction:
    action: str = NONE
    new_sl: float | None = None
    close_fraction: float = 0.0
    reason: str = ""


def decide_exit(*, buy: bool, entry: float, stop: float, bid: float, ask: float,
                opened_hours: float, initial_stop: float, break_even_after_r: float = 0.0,
                partial_tp_r: float = 0.0, partial_tp_pct: float = 0.0, partial_done: bool = False,
                max_hold_hours: float = 0.0) -> ExitAction:
    """Return the single most urgent exit action for a position.

    ``initial_stop`` is the stop placed at entry; it defines 1R. Current ``stop``
    may already have been trailed or moved to break-even.
    """
    price = bid if buy else ask
    r = abs(entry - initial_stop) if initial_stop else 0.0

    if max_hold_hours > 0 and opened_hours >= max_hold_hours:
        return ExitAction(TIME_EXIT, reason=f"time exit after {opened_hours:.1f}h")

    if r > 0 and partial_tp_r > 0 and partial_tp_pct > 0 and not partial_done:
        target = entry + partial_tp_r * r if buy else entry - partial_tp_r * r
        if (price >= target) if buy else (price <= target):
            return ExitAction(PARTIAL_TP, close_fraction=partial_tp_pct / 100.0,
                              reason=f"partial take-profit at {partial_tp_r}R")

    if r > 0 and break_even_after_r > 0:
        target = entry + break_even_after_r * r if buy else entry - break_even_after_r * r
        favorable = (price >= target) if buy else (price <= target)
        # Only move a stop that is still on the losing side of entry.
        can_improve = stop < entry if buy else (stop > entry or stop == 0)
        if favorable and can_improve:
            return ExitAction(BREAK_EVEN, new_sl=entry,
                              reason=f"stop moved to break-even after {break_even_after_r}R")
    return ExitAction()
