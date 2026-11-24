from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import BotLog, BotSettings, Notification, RiskSettings, Trade

RISK_MAP = {"perTrade": "risk_per_trade", "maxDaily": "max_daily_loss", "maxDD": "max_drawdown", "maxPos": "max_open_positions",
            "minRR": "min_risk_reward", "maxSpread": "max_spread_pips", "session": "session", "closeOnStop": "close_on_emergency",
            "trailingEnabled": "trailing_enabled", "trailingAtrMult": "trailing_atr_mult",
             "maxDailyTrades": "max_daily_trades", "maxConsecutiveLosses": "max_consecutive_losses",
             "lotMode": "lot_mode", "fixedLot": "fixed_lot", "maxLotSize": "max_lot_size",
              "breakEvenAfterR": "break_even_after_r", "partialTpR": "partial_tp_r",
              "partialTpPct": "partial_tp_pct", "maxHoldHours": "max_hold_hours",
              "maxCurrencyExposure": "max_currency_exposure"}
ENGINE_TIMEOUT = 30  # seconds without heartbeat => engine offline


def aware(dt: datetime | None) -> datetime | None:
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def get_bot(db: Session) -> BotSettings:
    return db.get(BotSettings, 1)


def get_risk(db: Session) -> RiskSettings:
    return db.get(RiskSettings, 1)


def engine_online(bot: BotSettings) -> bool:
    hb = aware(bot.heartbeat)
    return bool(hb and (datetime.now(timezone.utc) - hb).total_seconds() < ENGINE_TIMEOUT)


def add_log(db: Session, msg: str, level: str = "info") -> None:
    db.add(BotLog(level=level, message=msg))


def add_notification(db: Session, kind: str, msg: str) -> None:
    db.add(Notification(kind=kind, message=msg))


def iso(dt: datetime | None) -> str | None:
    dt = aware(dt)
    return dt.isoformat() if dt else None


def ser_trade(t: Trade) -> dict:
    return {"id": t.id, "ticket": t.ticket, "sym": t.symbol, "dir": t.type, "lot": t.volume, "entry": t.entry_price,
            "sl": t.stop_loss, "tp": t.take_profit, "exit": t.exit_price, "pnl": t.profit, "why": t.close_reason,
            "strat": f"EMA_RSI · {t.strategy}", "status": t.status, "openedAt": iso(t.opened_at), "closedAt": iso(t.closed_at),
            "time": iso(t.closed_at or t.opened_at)}


def ser_risk(r: RiskSettings) -> dict:
    return {k: getattr(r, v) for k, v in RISK_MAP.items()}


def trade_stats(trades: list[Trade]) -> dict:
    w = [t.profit for t in trades if t.profit > 0]
    l = [-t.profit for t in trades if t.profit <= 0]
    gp, gl = sum(w), sum(l)
    run = peak = dd = 0.0
    for t in sorted(trades, key=lambda x: x.closed_at or x.opened_at):
        run += t.profit
        peak = max(peak, run)
        dd = max(dd, peak - run)
    return {"trades": len(trades), "winRate": (len(w) / len(trades) * 100) if trades else 0.0, "grossProfit": gp,
            "grossLoss": gl, "net": gp - gl, "profitFactor": (gp / gl) if gl else None, "maxDrawdownMoney": dd}
