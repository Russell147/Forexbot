# ForexPilot AI: frontend

Next.js 15 (App Router) + TypeScript + Tailwind CSS.

## Run with the backend
1. Start the FastAPI backend at `http://localhost:8000`.
2. Copy `.env.local.example` to `.env.local` and keep `NEXT_PUBLIC_USE_SIMULATOR=false`.
3. Run `npm install` once, then `npm run dev` from this folder.
4. Open `http://localhost:3000` and create the first account. Backend registration is disabled after the first account unless `ALLOW_REGISTRATION=true`.

## Notes
- Set `NEXT_PUBLIC_USE_SIMULATOR=true` in `.env.local` to use the built-in simulator instead.
- The frontend polls the backend for account, trade, strategy, risk, and bot state. Market quotes and manual position closing are not exposed by the current API.
- The frontend never talks to MT5, and no MT5 passwords or API keys belong in this folder. The trading engine must be running on the MT5 machine for bot start requests to succeed.
- Deploy to Vercel; the trading engine runs separately on the Windows VPS.
