import pandas as pd


def report(trades: pd.DataFrame, start_equity: float, equity_curve: list[float], skipped: int = 0) -> dict:
    if trades.empty:
        return {"trades": 0, "skipped_min_lot": skipped}
    w, l = trades[trades.pnl > 0].pnl, trades[trades.pnl <= 0].pnl
    eq = pd.Series(equity_curve)
    return {"trades": len(trades), "win_rate_pct": round(len(w) / len(trades) * 100, 1), "net_profit": round(trades.pnl.sum(), 2),
            "return_pct": round(trades.pnl.sum() / start_equity * 100, 2),
            "profit_factor": round(w.sum() / -l.sum(), 2) if len(l) and l.sum() else None,
            "avg_win": round(w.mean(), 2) if len(w) else 0, "avg_loss": round(l.mean(), 2) if len(l) else 0,
            "expectancy": round(trades.pnl.mean(), 2), "max_drawdown_pct": round(((eq.cummax() - eq) / eq.cummax()).max() * 100, 2),
            "skipped_min_lot": skipped}
