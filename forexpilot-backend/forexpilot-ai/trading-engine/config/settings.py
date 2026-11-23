import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

ENGINE_DIR = Path(__file__).resolve().parents[1]
ROOT = ENGINE_DIR.parent

# Load the engine's .env explicitly. load_dotenv() alone uses the current working
# directory, so `python C:\...\trading-engine\main.py` from elsewhere silently
# missed DATABASE_URL and MT5_PATH.
load_dotenv(ENGINE_DIR / ".env")

for p in (ROOT / "backend", ROOT / "telegram-bot"):  # share DB models + notifier with the API
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _b(k: str, d: str = "false") -> bool:
    return os.getenv(k, d).strip().lower() in ("1", "true", "yes")


def _clean_path(raw: str) -> str:
    r"""Repair a Windows path whose `\t` was turned into a TAB by dotenv."""
    raw = raw.strip().strip("'\"")
    if "\t" in raw and "\\t" not in raw:
        raw = raw.replace("\t", "\\t")
    return raw


# The API defaults to a local SQLite database. Older engine .env files shipped
# with a placeholder Postgres URL; never overwrite a real DATABASE_URL, only
# replace the placeholder so engine + API share the same store.
_db_url = os.getenv("DATABASE_URL", "")
if "your_db_host" in _db_url.lower():
    _shared_db = ROOT / "backend" / "forexpilot.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{_shared_db.as_posix()}"

MT5_LOGIN = int(os.getenv("MT5_LOGIN") or 0)
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
MT5_PATH = _clean_path(os.getenv("MT5_PATH", ""))
SYMBOL_SUFFIX = os.getenv("SYMBOL_SUFFIX", "")
ALLOW_LIVE = _b("ALLOW_LIVE")
POLL_SECONDS = float(os.getenv("POLL_SECONDS", "5"))
MAGIC = int(os.getenv("MAGIC_NUMBER", "240611"))
DEVIATION = int(os.getenv("MAX_DEVIATION_POINTS", "20"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
AI_MIN_CONFIDENCE = float(os.getenv("AI_MIN_CONFIDENCE", "0.7"))

# Lightweight status server exposed by the engine. The API polls /health here.
ENGINE_API_HOST = os.getenv("ENGINE_API_HOST", "127.0.0.1")
ENGINE_API_PORT = int(os.getenv("ENGINE_API_PORT", "8001"))
