"""Hard demo-only safety gate.

Every order path must call :func:`assert_demo` immediately before submitting an
order to MT5. The check re-reads ``account_info()`` at order time instead of
trusting a cached connection-time flag, so a terminal switched to a live account
between scans can never place an order. Live trading is disabled unconditionally
in this build (``ALLOW_LIVE`` must remain false).
"""
import logging

import MetaTrader5 as mt5

from config import settings

log = logging.getLogger("mt5.demo_guard")

LIVE_DISABLED = "Live trading is disabled in this build (ALLOW_LIVE must remain false)"


def assert_demo() -> tuple[bool, str]:
    """Return (allowed, message). Allowed only for a confirmed DEMO account."""
    if settings.ALLOW_LIVE:
        log.error("Refusing order: ALLOW_LIVE is enabled")
        return False, LIVE_DISABLED
    try:
        account = mt5.account_info()
    except Exception as e:  # noqa: BLE001 - never let an IPC error slip through
        log.error("Could not verify MT5 account before order: %s", e)
        return False, f"cannot verify MT5 account: {type(e).__name__}: {e}"
    if account is None:
        log.error("Could not verify MT5 account before order: account_info returned None")
        return False, "cannot verify MT5 account (account_info unavailable)"
    if account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        log.error("Refusing order: account %s on %s is not a demo account (trade_mode=%s)",
                  account.login, account.server, account.trade_mode)
        return False, f"refusing to trade: MT5 account {account.login} on {account.server} is not a demo account"
    return True, "demo account verified"
