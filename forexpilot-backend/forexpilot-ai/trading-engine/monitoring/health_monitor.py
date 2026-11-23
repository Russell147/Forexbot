import logging

from app.models import BotLog, Notification
from config import settings

log = logging.getLogger("engine")


def add_log(db, msg: str, level: str = "info") -> None:
    getattr(log, "warning" if level == "warn" else level if level in ("info", "error") else "info")(msg)
    db.add(BotLog(level=level, message=msg))


def notify(db, bot, kind: str, msg: str) -> None:
    """Store a notification and push it to Telegram if enabled."""
    sent = False
    if bot.telegram_enabled:
        try:
            from notifications import send  # telegram-bot/notifications.py
            sent = send(msg)
        except Exception as e:  # never let notifications break trading
            log.warning("telegram failed: %s", e)
    db.add(Notification(kind=kind, message=msg, sent=sent))
