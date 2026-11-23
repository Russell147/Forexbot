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


def init_db() -> None:
    """Create tables (dev) and seed defaults. In production prefer `alembic upgrade head`."""
    from app import models  # noqa: F401
    from app.services.seed import seed

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
