# Architecture

Frontend (Vercel) -> FastAPI + PostgreSQL <- Trading engine (Windows VPS with MT5) -> MetaTrader 5 -> broker.

- Trading commands/state use PostgreSQL as the contract (`bot_settings.desired_state` down, heartbeat/positions/trades up). The API additionally polls the engine's read-only `/health` (default `127.0.0.1:8001`, set with `ENGINE_API_URL`) only for accurate connection status; it never sends orders over HTTP.
- The engine ALWAYS starts stopped and never auto-resumes after a restart.
- The engine refuses to trade a live account unless `ALLOW_LIVE=true`.
- Per-signal pipeline: closed-candle strategy signal -> conflict check -> risk checks (spread, session, duplicate, max positions, R:R, daily loss, drawdown) -> sizing (rejects if the minimum lot exceeds the risk budget) -> broker-rule validation -> optional Gemini veto -> `order_check` -> `order_send`. AI can only veto, never create or enlarge a trade.
- Secrets: MT5 password, Telegram token and Gemini key live only in `trading-engine/.env`.
- `market_data` table from the spec is intentionally not stored: candles come live from MT5 or from CSV for backtests.
