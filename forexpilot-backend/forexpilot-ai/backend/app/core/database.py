from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

_kw = {"connect_args": {"check_same_thread": False}} if settings.database_url.startswith("sqlite") else {"pool_pre_ping": True}
engine = create_engine(settings.database_url, **_kw)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _add_missing_columns() -> None:
    """Additive SQLite migration for newly introduced risk settings.

    ``create_all`` never alters existing tables, so older databases need these
    columns added explicitly. Existing values and all other tables are untouched.
    """
    from sqlalchemy import inspect, text

    wanted = {
        "max_daily_trades": "INTEGER DEFAULT 10",
        "max_consecutive_losses": "INTEGER DEFAULT 3",
        "lot_mode": "VARCHAR(10) DEFAULT 'risk'",
        "fixed_lot": "FLOAT DEFAULT 0.01",
        "max_lot_size": "FLOAT DEFAULT 0.10",
        "break_even_after_r": "FLOAT DEFAULT 1.0",
        "partial_tp_r": "FLOAT DEFAULT 0.0",
        "partial_tp_pct": "FLOAT DEFAULT 0.0",
        "max_hold_hours": "FLOAT DEFAULT 0.0",
        "max_currency_exposure": "INTEGER DEFAULT 2",
    }
    trade_wanted = {
        "initial_stop": "FLOAT",
        "partial_done": "BOOLEAN DEFAULT 0",
    }
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns("risk_settings")}
    trade_existing = {c["name"] for c in inspector.get_columns("trades")}
    with engine.begin() as conn:
        for name, ddl in wanted.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE risk_settings ADD COLUMN {name} {ddl}"))
        for name, ddl in trade_wanted.items():
            if name not in trade_existing:
                conn.execute(text(f"ALTER TABLE trades ADD COLUMN {name} {ddl}"))


def init_db() -> None:
    """Create tables (dev) and seed defaults. In production prefer `alembic upgrade head`."""
    from app import models  # noqa: F401
    from app.services.seed import seed

    Base.metadata.create_all(engine)
    _add_missing_columns()
    with SessionLocal() as db:
        seed(db)
