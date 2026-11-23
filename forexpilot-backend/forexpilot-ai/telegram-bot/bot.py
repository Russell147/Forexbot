"""Optional Telegram command bot: /status and /stop (emergency: blocks new trades). Only answers TELEGRAM_CHAT_ID.
Run next to the API:  python bot.py   (needs DATABASE_URL and the backend folder on the path, same as the engine)"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import requests
from dotenv import load_dotenv

load_dotenv()
from app.core.database import SessionLocal  # noqa: E402
from app.models import BotSettings, Trade  # noqa: E402

TOKEN, CHAT = os.getenv("TELEGRAM_BOT_TOKEN", ""), str(os.getenv("TELEGRAM_CHAT_ID", ""))
API = f"https://api.telegram.org/bot{TOKEN}"


def reply(text: str) -> None:
    requests.post(f"{API}/sendMessage", json={"chat_id": CHAT, "text": text}, timeout=10)


def handle(cmd: str) -> None:
    with SessionLocal() as db:
        b = db.get(BotSettings, 1)
        if cmd.startswith("/status"):
            n = db.query(Trade).filter_by(status="OPEN").count()
            reply(f"State: {b.actual_state} (wanted: {b.desired_state})\nMT5: {'connected' if b.mt5_connected else 'DOWN'}\nEquity: {b.equity:.2f}\nOpen positions: {n}")
        elif cmd.startswith("/stop"):
            b.desired_state, b.emergency_close_done = "emergency", False
            db.commit()
            reply("Emergency stop requested: no new trades. Open positions keep their SL/TP.")


def main() -> None:
    if not TOKEN or not CHAT:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    offset = 0
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"timeout": 30, "offset": offset}, timeout=40).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message", {})
                if str(m.get("chat", {}).get("id")) == CHAT and m.get("text"):
                    handle(m["text"])
        except requests.RequestException:
            time.sleep(5)


if __name__ == "__main__":
    main()
