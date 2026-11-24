"""Currency-exposure filter to avoid stacking the same macro bet.

A 3-position limit is meaningless if all three positions are long USD. This
module counts how many open positions touch each currency and rejects a new
signal when it would push any currency past the configured limit.
"""
from typing import Iterable


def pair_currencies(symbol: str) -> tuple[str, str]:
    """EURUSD.pro -> ('EUR', 'USD'). Unknown symbols contribute no exposure."""
    letters = "".join(c for c in str(symbol).upper() if c.isalpha())[:6]
    return (letters[:3], letters[3:6]) if len(letters) == 6 else ()


def currency_counts(symbols: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sym in symbols:
        for currency in pair_currencies(sym):
            counts[currency] = counts.get(currency, 0) + 1
    return counts


def check_correlation(new_symbol: str, open_symbols: Iterable[str], limit: int) -> str | None:
    """Reject when a new trade would exceed the per-currency position limit.

    ``limit <= 0`` disables the filter. Returns a rejection reason or None.
    """
    if limit <= 0:
        return None
    counts = currency_counts(open_symbols)
    for currency in pair_currencies(new_symbol):
        used = counts.get(currency, 0)
        if used + 1 > limit:
            return f"correlation filter: {currency} already in {used} open position(s) (limit {limit})"
    return None
