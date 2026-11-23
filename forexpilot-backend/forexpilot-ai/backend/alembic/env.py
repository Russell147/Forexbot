from alembic import context

from app import models  # noqa: F401
from app.core.database import Base, engine

target_metadata = Base.metadata


def run_migrations_online() -> None:
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()

DATABASE_URL = "sqlite:///../backend/forexpilot.db"
MT5_LOGIN = "5059236134"
MT5_PASSWORD = "Sk@4FuGi"
MT5_SERVER = ""
ALLOW_LIVE = "false"
