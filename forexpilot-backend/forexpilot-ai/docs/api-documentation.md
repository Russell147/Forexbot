# ForexPilot AI: API

Base URL: `http://localhost:8000` (matches `NEXT_PUBLIC_API_URL` in the frontend). Interactive docs: `/docs`.
Auth: JWT, sent as an httpOnly cookie (`credentials: "include"`) or `Authorization: Bearer <token>`.

| Method | Path | Purpose |
|---|---|---|
| POST | /auth/register | First user only (or if ALLOW_REGISTRATION=true) |
| POST | /auth/login | `{email, password}`; sets cookie, returns token |
| POST | /auth/logout, GET /auth/me | |
| GET | /state | Everything the dashboard needs in one poll (same field names as the frontend simulator: run, emg, bal, equity, pos, trades, risk, strat, on, logs) |
| GET | /bot/status | desired/actual state, engineOnline, mt5Connected |
| POST | /bot/start | Refused with 409 if the engine is offline or blocked on a live account |
| POST | /bot/stop | Stops new trades; open positions keep SL/TP |
| POST | /bot/emergency-stop | `{closePositions?: bool}`; blocks new trades immediately |
| GET | /positions, /trades?status=&limit= | |
| GET/PUT | /strategies, /strategies/{name} `{on}` | |
| GET/PUT | /settings, /settings/risk, /settings/pairs/{symbol} | Risk keys: perTrade, maxDaily, maxDD, maxPos, minRR, maxSpread, session, closeOnStop, trailingEnabled, trailingAtrMult |
| GET | /analytics | stats, byPair, equityCurve |
| GET/POST | /accounts | Metadata only; any `password` field is rejected |
| GET | /logs, /notifications | |
| GET | /health | Unauthenticated liveness |

How it works: the API only writes the *desired* state to `bot_settings`. The trading engine polls it every few seconds, writes its heartbeat, account snapshot, positions and trades back. Closing the dashboard or stopping the API never stops the engine.
