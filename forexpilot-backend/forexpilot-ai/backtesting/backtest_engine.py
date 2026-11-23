"""Bar-by-bar backtester for the EMA+RSI strategies.
Realism rules: signal on a CLOSED candle, entry at the NEXT open + spread + slippage, SL assumed first if SL and TP
share a candle, commission per lot, lot sizing from risk %. Data is treated as BID prices.
Usage: python backtest_engine.py --csv EURUSD_M15.csv --strategy "Day Trading" --spread 1.0"""
import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "trading-engine"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from historical_data import load_csv, synthetic  # noqa: E402
from performance_report import report  # noqa: E402
from strategies import REGISTRY  # noqa: E402


def run_backtest(df: pd.DataFrame, strategy, equity: float = 1000.0, risk_pct: float = 0.5, spread_pips: float = 1.0,
                 slippage_pips: float = 0.2, commission_per_lot: float = 7.0, pip: float = 0.0001, pip_value: float = 10.0,
                 min_lot: float = 0.01, lot_step: float = 0.01, min_rr: float = 2.0):
    d = strategy.compute(df.reset_index(drop=True))
    o, h, l, t = d["open"].values, d["high"].values, d["low"].values, d["time"].values
    sp, sl_slip = spread_pips * pip, slippage_pips * pip
    trades, curve, skipped, bal, i = [], [equity], 0, equity, strategy.warmup
    while i < len(d) - 2:
        s = strategy.signal_at(d, i)
        if not s.direction or s.tp_dist / s.sl_dist + 1e-9 < min_rr:
            i += 1
            continue
        buy = s.direction == "BUY"
        entry = o[i + 1] + sp + sl_slip if buy else o[i + 1] - sl_slip
        sl = entry - s.sl_dist if buy else entry + s.sl_dist
        tp = entry + s.tp_dist if buy else entry - s.tp_dist
        lot = math.floor(bal * risk_pct / 100 / (s.sl_dist / pip * pip_value) / lot_step) * lot_step
        if lot < min_lot:
            skipped += 1
            i += 1
            continue
        exit_px, j, why = None, i + 1, "End of data"
        while j < len(d):
            hit_sl = l[j] <= sl if buy else h[j] + sp >= sl
            hit_tp = h[j] >= tp if buy else l[j] + sp <= tp
            if hit_sl:  # SL wins ties (conservative)
                exit_px, why = (sl - sl_slip if buy else sl + sl_slip), "Stop-loss"
                break
            if hit_tp:
                exit_px, why = tp, "Take-profit"
                break
            j += 1
        if exit_px is None:
            break
        pnl = ((exit_px - entry) if buy else (entry - exit_px)) / pip * pip_value * lot - commission_per_lot * lot
        bal += pnl
        trades.append({"open": t[i + 1], "close": t[j], "dir": s.direction, "lot": round(lot, 2), "entry": entry, "exit": exit_px, "pnl": pnl, "why": why})
        curve.append(bal)
        i = j + 1
    tr = pd.DataFrame(trades)
    return tr, report(tr, equity, curve, skipped)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv"); ap.add_argument("--strategy", default="Day Trading", choices=list(REGISTRY))
    ap.add_argument("--equity", type=float, default=1000); ap.add_argument("--risk", type=float, default=0.5)
    ap.add_argument("--spread", type=float, default=1.0); ap.add_argument("--slippage", type=float, default=0.2)
    ap.add_argument("--commission", type=float, default=7.0); ap.add_argument("--pip", type=float, default=0.0001)
    a = ap.parse_args()
    data = load_csv(a.csv) if a.csv else synthetic()
    if not a.csv:
        print("No --csv given: using SYNTHETIC random data (pipeline test only).")
    _, rep = run_backtest(data, REGISTRY[a.strategy](), a.equity, a.risk, a.spread, a.slippage, a.commission, a.pip)
    for k, v in rep.items():
        print(f"{k:>18}: {v}")
