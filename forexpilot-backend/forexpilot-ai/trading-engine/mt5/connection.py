import logging
import os

import MetaTrader5 as mt5

from config import settings

log = logging.getLogger("mt5")


def _last_error() -> str:
    code, text = mt5.last_error()
    return f"{text} (code {code})" if code else str(text)


class MT5Connection:
    """Owns the single MT5 IPC connection. All calls happen on the engine thread."""

    def __init__(self) -> None:
        self.last_error = ""
        self.info: dict = {}

    def _fail(self, message: str) -> bool:
        self.last_error = message
        log.error("%s", message)
        return False

    def _remember_account(self, account) -> None:
        demo = account.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
        self.info = {
            "login": account.login,
            "server": account.server,
            "type": "demo" if demo else "live",
            "balance": float(account.balance),
            "equity": float(account.equity),
            "demo": demo,
        }

    def connect(self) -> bool:
        self.last_error = ""
        if settings.MT5_PATH and not os.path.isfile(settings.MT5_PATH):
            return self._fail(f"MT5_PATH does not exist: {settings.MT5_PATH!r}")

        kw: dict = {}
        if settings.MT5_PATH:
            kw["path"] = settings.MT5_PATH
        # Passing an empty server makes mt5.initialize() fail. Only log in
        # explicitly when all credentials are present; otherwise attach to the
        # account already logged in to the desktop terminal (demo testing).
        if settings.MT5_LOGIN and settings.MT5_PASSWORD and settings.MT5_SERVER:
            kw.update(login=settings.MT5_LOGIN, password=settings.MT5_PASSWORD, server=settings.MT5_SERVER)
        elif any((settings.MT5_LOGIN, settings.MT5_PASSWORD, settings.MT5_SERVER)):
            log.warning("MT5 credentials incomplete (MT5_SERVER is empty); using the account already logged in to the terminal")

        try:
            ok = mt5.initialize(**kw)
        except Exception as e:  # noqa: BLE001 - surface a clear error to the dashboard
            return self._fail(f"MT5 initialize raised {type(e).__name__}: {e}")
        if not ok:
            return self._fail(f"MT5 initialize failed: {_last_error()}")

        ti = mt5.terminal_info()
        if ti is None:
            mt5.shutdown()
            return self._fail(f"MT5 terminal info unavailable: {_last_error()}")
        if not ti.connected:
            mt5.shutdown()
            return self._fail("MT5 terminal is not connected to the broker. Start MetaTrader 5 and log in to a DEMO account.")
        account = mt5.account_info()
        if account is None:
            mt5.shutdown()
            return self._fail("No MT5 account is logged in. Log in to a DEMO account in the terminal.")
        self._remember_account(account)
        log.info("MT5 connected: login=%s server=%s account=%s", account.login, account.server, self.info["type"])
        return True

    def reconnect(self) -> bool:
        try:
            mt5.shutdown()
        except Exception:  # noqa: BLE001 - shutdown must never block a retry
            log.exception("MT5 shutdown failed during reconnect")
        return self.connect()

    def is_connected(self) -> bool:
        try:
            ti = mt5.terminal_info()
            if ti is None:
                self.last_error = f"MT5 terminal unavailable: {_last_error()}"
                return False
            if not ti.connected:
                self.last_error = "MT5 terminal is not connected to the broker"
                return False
            account = mt5.account_info()
            if account is None:
                self.last_error = "No MT5 account is logged in"
                return False
            self._remember_account(account)
            self.last_error = ""
            return True
        except Exception as e:  # noqa: BLE001
            self.last_error = f"MT5 status check failed: {type(e).__name__}: {e}"
            return False

    def status(self) -> dict:
        connected = self.is_connected()
        return {
            "initialized": connected,
            "connected": connected,
            "mt5_connected": connected,
            "account": dict(self.info),
            "error": self.last_error or None,
            "demo": self.info.get("demo", False),
            "live_trading_allowed": settings.ALLOW_LIVE,
        }

    @staticmethod
    def account():
        return mt5.account_info()

    def is_demo(self) -> bool:
        return bool(self.info.get("demo")) if self.info else bool(
            (a := mt5.account_info()) and a.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
        )
