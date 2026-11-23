# ForexPilot AI: backend, engine, tools

    backend/        FastAPI + SQLAlchemy + Alembic (API, auth, settings, state)
    trading-engine/ MT5 engine (Windows). Strategies, risk, execution, AI veto, sync
    telegram-bot/   notifications.py (used by the engine) and bot.py (/status, /stop)
    backtesting/    bar-by-bar backtester with spread, slippage, commission
    database/       schema.sql (PostgreSQL), migrations notes
    docs/           API + architecture

## 1. Database + API (any server)
    cp .env.example .env && cp backend/.env.example backend/.env   # set POSTGRES_PASSWORD and SECRET_KEY
    docker compose up --build
    curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" -d '{"email":"you@example.com","password":"a-long-password"}'
(Without Docker: `cd backend && pip install -r requirements.txt && uvicorn app.main:app`; SQLite is the dev default.)

## 2. Trading engine (Windows with MetaTrader 5 installed and logged in to a DEMO account)
    cd trading-engine && pip install -r requirements.txt
    copy .env.example .env    # DATABASE_URL (same DB as the API), MT5_LOGIN/PASSWORD/SERVER, MT5_PATH
    python main.py
Then press Start in the dashboard. Keep the machine/VPS running; the website is not needed for trading.
The engine also serves a read-only status API at `http://127.0.0.1:8001/health` (check with `curl http://127.0.0.1:8001/health`). Set `ENGINE_API_URL` in the backend environment if the engine runs on another host.

## 3. Connect the frontend
In the frontend project, copy `.env.local.example` to `.env.local`, keep `NEXT_PUBLIC_API_URL=http://localhost:8000` and `NEXT_PUBLIC_USE_SIMULATOR=false`, then run `npm run dev`. Open `http://localhost:3000` and create the first account. The dashboard reads API state and sends bot and settings actions to this backend; start the trading engine on the MT5 machine before requesting bot start. See `docs/api-documentation.md` for the endpoints and limitations.

## 4. Tests / backtest
    cd backend && pytest
    cd backtesting && python backtest_engine.py --csv EURUSD_M15.csv --strategy "Day Trading" --spread 1.0

## Read before trading
- Demo first. The EMA+RSI strategy is an unproven baseline; backtest on real data and demo-trade for weeks.
- Small accounts: if the broker's minimum lot risks more than your risk-per-trade, the engine REJECTS the trade rather than oversize it. With $20-$50 and 0.5% risk it will rarely trade; use a cent account or accept a higher risk setting knowingly.
- Session hours are UTC. Verify symbol names/suffix, filling modes and stop levels with your broker.
- The engine was not run against a live MT5 terminal in this build environment (Linux). Test on a demo account first.
