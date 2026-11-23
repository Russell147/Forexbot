"""Server-side view of the trading engine's read-only status API.

The browser keeps talking only to this FastAPI backend; the backend knows the
engine URL from ENGINE_API_URL. No MT5 credentials or DB secrets are returned.
"""
import threading
import time

import httpx

from app.core.config import settings

CACHE_SECONDS = 2.0
TIMEOUT_SECONDS = 1.5

_lock = threading.Lock()
_cached: dict = {"at": 0.0, "data": None}

_OFFLINE = "Trading engine is offline. Start trading-engine/main.py on the MT5 machine first."


def _base(**changes) -> dict:
    data = {
        "state": "disconnected",
        "engine_online": False,
        "mt5_connected": False,
        "message": _OFFLINE,
        "last_tick": None,
        "account": {},
        "live_trading_allowed": False,
        "trading_state": None,
        "analysis": {},
        "analysis_at": None,
    }
    data.update(changes)
    return data


def _interpret(payload: dict) -> dict:
    state = payload.get("state")
    if state not in ("connected", "disconnected", "connecting", "error"):
        state = "connected" if payload.get("engine_online") and payload.get("mt5_connected") else "disconnected"
    if state == "connected":
        message = "MT5 connected and trading engine is online"
    elif state == "connecting":
        message = "Connecting to the trading engine..."
    elif state == "error":
        message = payload.get("last_error") or payload.get("mt5_error") or "MT5 connection error in the trading engine"
    else:
        message = _OFFLINE
    return _base(
        state=state,
        engine_online=bool(payload.get("engine_online")),
        mt5_connected=bool(payload.get("mt5_connected")),
        message=message,
        last_tick=payload.get("last_tick"),
        account=payload.get("account") or {},
        live_trading_allowed=bool(payload.get("live_trading_allowed")),
        trading_state=payload.get("trading_state"),
        analysis=payload.get("analysis") or {},
        analysis_at=payload.get("analysis_at"),
    )


def get_engine_status(force: bool = False) -> dict:
    """Return cached engine status; refresh at most every CACHE_SECONDS."""
    now = time.monotonic()
    with _lock:
        cached = _cached["data"]
        if not force and cached is not None and now - _cached["at"] < CACHE_SECONDS:
            return dict(cached)
        # Let concurrent readers see a "connecting" state while a poll is in flight.
        _cached["data"] = _base(state="connecting", message="Connecting to the trading engine...")

    url = settings.engine_api_url.rstrip("/") + "/health"
    try:
        response = httpx.get(url, timeout=TIMEOUT_SECONDS)
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code >= 400 and not payload:
            data = _base(state="disconnected", message=f"Trading engine returned HTTP {response.status_code}")
        else:
            data = _interpret(payload)
    except Exception as e:  # noqa: BLE001 - network errors are expected when the engine is down
        detail = "connection refused" if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout)) else type(e).__name__
        data = _base(state="disconnected", message=f"Cannot reach the trading engine ({detail})")

    with _lock:
        _cached.update(at=time.monotonic(), data=data)
    return dict(data)
