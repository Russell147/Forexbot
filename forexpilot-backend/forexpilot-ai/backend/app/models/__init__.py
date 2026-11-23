from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


DT = DateTime(timezone=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DT, default=utcnow)


class TradingAccount(Base):
    """Metadata only. MT5 passwords live in the engine's environment, never in the database."""
    __tablename__ = "trading_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    login: Mapped[int] = mapped_column(BigInteger)
    server: Mapped[str] = mapped_column(String(100), default="")
    broker: Mapped[str] = mapped_column(String(100), default="")
    account_type: Mapped[str] = mapped_column(String(10), default="demo")
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DT, default=utcnow)


class Strategy(Base):
    __tablename__ = "strategies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    timeframes: Mapped[str] = mapped_column(String(50))
    params: Mapped[dict] = mapped_column(JSON, default=dict)


class TradingPair(Base):
    __tablename__ = "trading_pairs"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), unique=True)
    description: Mapped[str] = mapped_column(String(80), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class TradingSignal(Base):
    __tablename__ = "trading_signals"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(12), index=True)
    strategy: Mapped[str] = mapped_column(String(50))
    timeframe: Mapped[str] = mapped_column(String(5))
    direction: Mapped[str] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(12))  # EXECUTED / REJECTED
    reason: Mapped[str] = mapped_column(Text, default="")
    ai_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DT, default=utcnow)


class Trade(Base):
    """One row per trade. status=OPEN rows are the live positions."""
    __tablename__ = "trades"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    symbol: Mapped[str] = mapped_column(String(12), index=True)
    type: Mapped[str] = mapped_column(String(4))
    volume: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(8), default="OPEN", index=True)
    strategy: Mapped[str] = mapped_column(String(50), default="")
    close_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DT, default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DT, nullable=True)


class RiskSettings(Base):
    __tablename__ = "risk_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    risk_per_trade: Mapped[float] = mapped_column(Float, default=0.5)
    max_daily_loss: Mapped[float] = mapped_column(Float, default=2.0)
    max_drawdown: Mapped[float] = mapped_column(Float, default=5.0)
    max_open_positions: Mapped[int] = mapped_column(Integer, default=3)
    min_risk_reward: Mapped[float] = mapped_column(Float, default=2.0)
    max_spread_pips: Mapped[float] = mapped_column(Float, default=1.5)
    session: Mapped[str] = mapped_column(String(30), default="All sessions")
    trailing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    trailing_atr_mult: Mapped[float] = mapped_column(Float, default=1.5)
    close_on_emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    max_daily_trades: Mapped[int] = mapped_column(Integer, default=10)
    max_consecutive_losses: Mapped[int] = mapped_column(Integer, default=3)


class Performance(Base):
    __tablename__ = "performance"
    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DT, default=utcnow, index=True)
    balance: Mapped[float] = mapped_column(Float)
    equity: Mapped[float] = mapped_column(Float)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DT, default=utcnow)


class BotLog(Base):
    __tablename__ = "bot_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(10), default="info")
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DT, default=utcnow, index=True)


class BotSettings(Base):
    """Single row (id=1). The API writes desired_state; the engine writes everything else."""
    __tablename__ = "bot_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    desired_state: Mapped[str] = mapped_column(String(12), default="stopped")  # stopped | running | emergency
    actual_state: Mapped[str] = mapped_column(String(14), default="stopped")   # + blocked_live
    emergency_close_done: Mapped[bool] = mapped_column(Boolean, default=False)
    heartbeat: Mapped[datetime | None] = mapped_column(DT, nullable=True)
    mt5_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    account_login: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    account_type: Mapped[str] = mapped_column(String(10), default="")
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    equity: Mapped[float] = mapped_column(Float, default=0.0)
    peak_equity: Mapped[float] = mapped_column(Float, default=0.0)
    day_start_equity: Mapped[float] = mapped_column(Float, default=0.0)
    day_start_date: Mapped[str] = mapped_column(String(10), default="")
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
