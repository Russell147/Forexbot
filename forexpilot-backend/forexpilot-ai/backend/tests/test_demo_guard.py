"""Safety gate tests: every order path refuses non-demo accounts.

``assert_demo`` is the single most important function in this project. These
tests override the MT5 account at check time and verify that LIVE accounts,
unknown accounts, IPC failures and ALLOW_LIVE=True are all rejected.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "trading-engine"))

import MetaTrader5 as mt5  # noqa: E402

from config import settings  # noqa: E402
from mt5 import demo_guard  # noqa: E402

DEMO = SimpleNamespace(login=5059236134, server="MetaQuotes-Demo",
                       trade_mode=mt5.ACCOUNT_TRADE_MODE_DEMO)
LIVE = SimpleNamespace(login=12345678, server="Real-Broker-Live",
                       trade_mode=mt5.ACCOUNT_TRADE_MODE_REAL)


@pytest.fixture(autouse=True)
def _force_live_disabled(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_LIVE", False, raising=False)
    yield


def test_demo_account_allowed(monkeypatch):
    monkeypatch.setattr(mt5, "account_info", lambda: DEMO)
    ok, msg = demo_guard.assert_demo()
    assert ok and "verified" in msg


@pytest.mark.parametrize("account", [LIVE, None])
def test_live_or_unknown_account_rejected(monkeypatch, account):
    monkeypatch.setattr(mt5, "account_info", lambda: account)
    ok, msg = demo_guard.assert_demo()
    assert not ok and msg


def test_account_info_exception_rejected(monkeypatch):
    def boom():
        raise RuntimeError("IPC disconnected")
    monkeypatch.setattr(mt5, "account_info", boom)
    ok, msg = demo_guard.assert_demo()
    assert not ok and "cannot verify" in msg


def test_allow_live_flag_never_permits_order(monkeypatch):
    # Even if the flag is accidentally enabled, the build must refuse.
    monkeypatch.setattr(settings, "ALLOW_LIVE", True)
    monkeypatch.setattr(mt5, "account_info", lambda: DEMO)
    ok, msg = demo_guard.assert_demo()
    assert not ok and msg == demo_guard.LIVE_DISABLED
