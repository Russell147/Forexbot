"""ForexPilot trading engine. Run on the Windows machine with MetaTrader 5 installed:  python main.py
Controlled by the API through the bot_settings table. It ALWAYS starts stopped: press Start in the dashboard.

A small read-only status API (default http://127.0.0.1:8001) is served on a daemon
thread so the dashboard/API can see real engine + MT5 state instead of guessing
from a stale database heartbeat.
"""
import json
import logging
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from config import settings  # noqa: F401  (loads .env, adjusts sys.path)

import MetaTrader5 as mt5
from app.core.database import SessionLocal, init_db
from app.models import BotSettings, RiskSettings, Strategy, TradingPair
from execution.trade_manager import try_trade
from indicators.atr import atr
from monitoring.health_monitor import add_log, notify
from monitoring.performance_tracker import snapshot, sync_positions
from mt5 import market_data as md
from mt5.connection import MT5Connection
from mt5.position_manager import apply_trailing, close_position, open_positions
from risk.risk_manager import limit_breach
from strategies import REGISTRY

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("engine")

conn = MT5Connection()
last_candle: dict[tuple, object] = {}
live_blocked = False
was_connected = False
last_snap = 0.0
last_retry = 0.0

# Published by the engine thread, read by the status HTTP thread. Never holds secrets.
STATUS: dict = {
    "started_at": time.time(),
    "last_tick": 0.0,
    "last_error": None,
    "mt5_connected": False,
    "mt5_error": None,
    "account": {},
    "trading_state": "stopped",
}
STATUS_LOCK = threading.Lock()


def update_status(**changes) -> None:
    with STATUS_LOCK:
        STATUS.update(changes)


def status_payload() -> dict:
    """Liveness + MT5 readiness. 200 only while the engine loop is alive."""
    with STATUS_LOCK:
        snap = dict(STATUS)
    now = time.time()
    grace = max(15.0, settings.POLL_SECONDS * 3)
    starting = snap["last_tick"] == 0.0 and now - snap["started_at"] < grace
    fresh = starting or (snap["last_tick"] > 0 and now - snap["last_tick"] <= grace)
    mt5_ok = bool(snap["mt5_connected"])
    error = snap["last_error"] or snap["mt5_error"]
    if not fresh and not error:
        error = "Engine loop has stopped reporting (no recent heartbeat)"
    if not fresh:
        state = "connecting" if starting else "disconnected"
    elif error or not mt5_ok:
        state = "error"
    else:
        state = "connected"
    return {
        "status": "ok" if fresh and mt5_ok and not error else ("error" if fresh else "unavailable"),
        "state": state,
        "engine_online": fresh,
        "mt5_connected": mt5_ok,
        "mt5_error": snap["mt5_error"],
        "last_error": error,
        "last_tick": datetime.fromtimestamp(snap["last_tick"], timezone.utc).isoformat() if snap["last_tick"] else None,
        "started_at": datetime.fromtimestamp(snap["started_at"], timezone.utc).isoformat(),
        "uptime_seconds": round(now - snap["started_at"], 1),
        "trading_state": snap["trading_state"],
        "account": snap["account"],
        "live_trading_allowed": settings.ALLOW_LIVE,
        "api": {"host": settings.ENGINE_API_HOST, "port": settings.ENGINE_API_PORT},
    }


class StatusHandler(BaseHTTPRequestHandler):
    server_version = "ForexPilotEngine/1.0"

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
            # A poller closing the connection early is normal; don't spam the log.
            log.debug("status API client disconnected before response was read")

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlsplit(self.path).path
        payload = status_payload()
        if path in ("/health", "/status"):
            self._send(200 if payload["engine_online"] else 503, payload)
        elif path == "/":
            self._send(200, {"name": "ForexPilot trading engine", "health": "/health", "status": "/status"})
        else:
            self._send(404, {"detail": "not found"})

    def log_message(self, fmt: str, *args) -> None:
        log.debug("status API %s", fmt % args)


def start_status_server() -> ThreadingHTTPServer | None:
    try:
        server = ThreadingHTTPServer((settings.ENGINE_API_HOST, settings.ENGINE_API_PORT), StatusHandler)
    except OSError as e:
        log.error("Status API failed to bind %s:%s: %s", settings.ENGINE_API_HOST, settings.ENGINE_API_PORT, e)
        return None
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, name="engine-status", daemon=True).start()
    log.info("Engine status API listening on http://%s:%s/health", settings.ENGINE_API_HOST, settings.ENGINE_API_PORT)
    return server


def scan(db, bot, risk) -> None:
    """Evaluate enabled strategies on newly closed candles and execute allowed signals."""
    pairs = [p.symbol for p in db.query(TradingPair).filter_by(enabled=True)]
    strats = db.query(Strategy).filter_by(enabled=True).all()
    live = open_positions()
    open_syms = {md.base_symbol(p.symbol) for p in live}
    for sym in pairs:
        md.ensure_symbol(sym)
        found = []  # (strategy name, tf, signal, df)
        for row in strats:
            cls = REGISTRY.get(row.name)
            if not cls:
                continue
            strat = cls(**(row.params or {}))
            for tf in cls.timeframes:
                df = md.get_rates(sym, tf, 300)
                if df is None or len(df) < strat.warmup + 5:
                    continue
                closed = df.iloc[:-1]  # drop the still-forming candle
                key, ct = (row.name, sym, tf), closed["time"].iloc[-1]
                if key not in last_candle:  # warm-up: never act on a candle that closed before we started watching
                    last_candle[key] = ct
                    continue
                if last_candle[key] == ct:
                    continue
                last_candle[key] = ct
                sig = strat.evaluate(closed)
                if sig.direction:
                    found.append((row.name, tf, sig, closed))
        if not found:
            continue
        if len({f[2].direction for f in found}) > 1:
            add_log(db, f"WAIT {sym}: strategies give conflicting signals")
            continue
        name, tf, sig, df = found[0]
        if try_trade(db, bot, risk, sym, name, tf, sig, df, len(live), sym in open_syms):
            live, open_syms = open_positions(), open_syms | {sym}


def manage_trailing(risk) -> None:
    if not risk.trailing_enabled:
        return
    for p in open_positions():
        df = md.get_rates(md.base_symbol(p.symbol), "M15", 60)
        if df is not None:
            apply_trailing(p, float(atr(df.iloc[:-1]).iloc[-1]), risk.trailing_atr_mult)


def tick() -> None:
    global was_connected, live_blocked, last_snap, last_retry
    state = conn.status()
    update_status(last_error=None, mt5_connected=state["connected"], mt5_error=state["error"], account=state["account"])
    bot = None
    try:
        with SessionLocal() as db:
            bot, risk = db.get(BotSettings, 1), db.get(RiskSettings, 1)
            bot.heartbeat = datetime.now(timezone.utc)
            if not conn.is_connected():
                if was_connected:
                    was_connected = False
                    notify(db, bot, "connection_lost", "MT5 connection lost")
                    add_log(db, "MT5 connection lost", "error")
                bot.mt5_connected, bot.actual_state = False, "stopped"
                if time.time() - last_retry > 15:
                    last_retry = time.time()
                    conn.reconnect()
                db.commit()
                return
            if not was_connected:
                was_connected = True
                live_blocked = (not conn.is_demo()) and not settings.ALLOW_LIVE
                notify(db, bot, "mt5_connected", f"MT5 connected ({'LIVE' if not conn.is_demo() else 'demo'} account)")
                if live_blocked:
                    add_log(db, "LIVE account detected and ALLOW_LIVE is false: trading blocked", "error")
            a = conn.account()
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            bot.mt5_connected, bot.account_login, bot.account_type = True, a.login, "demo" if conn.is_demo() else "live"
            bot.balance, bot.equity = a.balance, a.equity
            if bot.day_start_date != today or bot.day_start_equity <= 0:
                bot.day_start_date, bot.day_start_equity = today, a.equity
            bot.peak_equity = max(bot.peak_equity, a.equity)
            sync_positions(db, bot)
            if time.time() - last_snap > 60:
                last_snap = time.time()
                snapshot(db, a.balance, a.equity)

            if bot.desired_state == "emergency":
                if risk.close_on_emergency and not bot.emergency_close_done:
                    n = sum(close_position(p, "emergency") for p in open_positions())
                    add_log(db, f"Emergency: closed {n} position(s)", "warn")
                if not bot.emergency_close_done:
                    notify(db, bot, "emergency", "EMERGENCY STOP active: no new trades")
                bot.emergency_close_done, bot.actual_state = True, "emergency"
                last_candle.clear()
                db.commit()
                return
            if live_blocked:
                bot.actual_state, bot.desired_state = "blocked_live", "stopped"
                db.commit()
                return
            manage_trailing(risk)
            if bot.desired_state != "running":
                bot.actual_state = "stopped"
                last_candle.clear()  # so a restart never trades on a stale candle
                db.commit()
                return
            if (b := limit_breach(risk, a.equity, bot.day_start_equity, bot.peak_equity)):
                bot.desired_state, bot.actual_state = "stopped", "stopped"
                add_log(db, f"{b} - trading halted", "warn")
                notify(db, bot, "limit", f"{b} - trading halted")
                db.commit()
                return
            if bot.actual_state != "running":
                bot.actual_state = "running"
                notify(db, bot, "started", "Bot started")
            scan(db, bot, risk)
            db.commit()
    except KeyboardInterrupt:
        raise
    except Exception as e:  # noqa: BLE001 - keep the loop alive, report the error
        log.exception("tick failed")
        update_status(last_error=f"{type(e).__name__}: {e}")
    finally:
        update_status(last_tick=time.time())
        if bot is not None:
            try:
                update_status(trading_state=bot.actual_state)
            except Exception:  # noqa: BLE001 - detached ORM instance, ignore
                pass


def main() -> None:
    server = start_status_server()
    init_db()
    with SessionLocal() as db:
        bot = db.get(BotSettings, 1)
        # Safety: never auto-resume after a restart. The user must press Start again.
        bot.desired_state, bot.actual_state, bot.emergency_close_done = "stopped", "stopped", False
        add_log(db, "Engine started. Trading is OFF until Start is pressed in the dashboard.")
        db.commit()
    if not conn.connect():
        update_status(last_error=conn.last_error)
        log.error("Could not initialise MT5 yet; will keep retrying: %s", conn.last_error)
    else:
        st = conn.status()
        update_status(mt5_connected=st["connected"], mt5_error=st["error"], account=st["account"], last_error=None)
    try:
        while True:
            try:
                tick()
            except KeyboardInterrupt:
                break
            time.sleep(settings.POLL_SECONDS)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        mt5.shutdown()


if __name__ == "__main__":
    main()
