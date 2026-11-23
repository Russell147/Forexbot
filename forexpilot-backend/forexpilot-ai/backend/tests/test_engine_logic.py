import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "trading-engine"), str(ROOT / "backtesting")]

from datetime import datetime, timezone  # noqa: E402

from backtest_engine import run_backtest  # noqa: E402
from execution.execution_validator import validate_order  # noqa: E402
from historical_data import synthetic  # noqa: E402
from risk.position_sizing import lot_size  # noqa: E402
from risk.risk_manager import check_new_trade, limit_breach  # noqa: E402
from strategies import REGISTRY  # noqa: E402

INFO = SimpleNamespace(trade_tick_size=0.00001, trade_tick_value=1.0, volume_min=0.01, volume_max=100, volume_step=0.01,
                       trade_stops_level=10, point=0.00001, trade_mode=4)
RISK = SimpleNamespace(max_daily_loss=2, max_drawdown=5, max_open_positions=3, min_risk_reward=2, max_spread_pips=1.5, session="All sessions")
OK = dict(open_count=0, symbol_open=False, spread_pips=1.0, rr=2.0, equity=1000, day_start=1000, peak=1000)


def test_position_sizing():
    vol, _ = lot_size(10000, 0.5, 1.1, 1.098, INFO)  # $50 risk, 200 pips... 20 pips => $200/lot
    assert vol == 0.25
    vol, why = lot_size(30, 0.5, 1.1, 1.098, INFO)  # tiny account: min lot too risky -> refuse
    assert vol is None and "minimum lot" in why


def test_risk_rules():
    assert check_new_trade(RISK, **OK) is None
    assert "duplicate" in check_new_trade(RISK, **{**OK, "symbol_open": True})
    assert "spread" in check_new_trade(RISK, **{**OK, "spread_pips": 3})
    assert "risk/reward" in check_new_trade(RISK, **{**OK, "rr": 1.2})
    assert "max open" in check_new_trade(RISK, **{**OK, "open_count": 3})
    assert "Daily loss" in limit_breach(RISK, 975, 1000, 1000)
    assert "drawdown" in limit_breach(RISK, 940, 1000, 1000) or "Daily" in limit_breach(RISK, 940, 1000, 1000)
    assert check_new_trade(SimpleNamespace(**{**RISK.__dict__, "session": "London"}), **OK, now=datetime(2024, 1, 1, 3, tzinfo=timezone.utc))


def test_validator():
    assert validate_order(INFO, "BUY", 0.1, 1.1, 1.09, 1.12) is None
    assert validate_order(INFO, "BUY", 0.1, 1.1, 1.11, 1.12)
    assert validate_order(INFO, "SELL", 0.1, 1.1, 0, 1.08)


def test_backtest_runs_and_no_lookahead():
    df = synthetic(6000)
    tr, rep = run_backtest(df, REGISTRY["Day Trading"](), equity=10000)
    assert rep["trades"] > 5 and rep["max_drawdown_pct"] >= 0
    s = REGISTRY["Day Trading"]()
    d = s.compute(df)
    # a signal at candle i must not change if future candles are removed
    for i in range(200, 4000, 37):
        a = s.signal_at(d, i).direction
        b = s.signal_at(s.compute(df.iloc[: i + 1].reset_index(drop=True)), i).direction
        assert a == b
