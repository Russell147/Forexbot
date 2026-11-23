import type { Risk } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ApiTrade {
  id: number;
  sym: string;
  dir: "BUY" | "SELL";
  lot: number;
  entry: number;
  sl: number;
  tp: number;
  exit: number | null;
  pnl: number;
  why: string | null;
  strat: string;
  status: "OPEN" | "CLOSED";
  time: string | null;
}

export interface ApiEngine {
  state: "connected" | "disconnected" | "connecting" | "error";
  engine_online: boolean;
  mt5_connected: boolean;
  message: string | null;
  last_tick: string | null;
  account: { login?: number; server?: string; type?: string; demo?: boolean };
  live_trading_allowed: boolean;
  trading_state?: string | null;
}

export interface ApiState {
  run: boolean;
  emg: boolean;
  engineOnline: boolean;
  mt5Connected: boolean;
  bal: number;
  equity: number;
  peak: number;
  dayStartEquity: number;
  account: { login: number | null; type: string | null };
  engine?: ApiEngine;
  pos: ApiTrade[];
  trades: ApiTrade[];
  risk: Risk;
  tgm: boolean;
  strat: Record<string, { on: boolean; tf: string }>;
  on: Record<string, boolean>;
  logs: { t: string | null; m: string }[];
}

export interface ApiAnalytics {
  trades: number;
  winRate: number;
  grossProfit: number;
  grossLoss: number;
  net: number;
  profitFactor: number | null;
  maxDrawdownMoney: number;
  byPair: Record<string, number>;
  equityCurve: { t: string | null; balance: number; equity: number }[];
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    credentials: "include",
  });
  const text = await res.text();
  const body: unknown = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = typeof body === "object" && body !== null && "detail" in body
      ? String(body.detail)
      : `${res.status} ${res.statusText}`;
    throw new Error(detail);
  }
  return body as T;
}

const json = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  login: (email: string, password: string) => req<{ access_token: string }>("/auth/login", json({ email, password })),
  register: (email: string, password: string) => req<{ id: number; email: string }>("/auth/register", json({ email, password })),
  me: () => req<{ id: number; email: string; isAdmin: boolean }>("/auth/me"),
  logout: () => req<{ ok: boolean }>("/auth/logout", { method: "POST" }),
  state: () => req<ApiState>("/state"),
  engineHealth: (refresh = false) => req<ApiEngine>(`/engine/health${refresh ? "?refresh=true" : ""}`),
  analytics: () => req<ApiAnalytics>("/analytics"),
  botStart: () => req("/bot/start", { method: "POST" }),
  botStop: () => req("/bot/stop", { method: "POST" }),
  emergencyStop: (closePositions: boolean) => req("/bot/emergency-stop", json({ closePositions })),
  setStrategy: (name: string, on: boolean) =>
    req(`/strategies/${encodeURIComponent(name)}`, { method: "PUT", body: JSON.stringify({ on }) }),
  setRisk: (risk: Partial<Risk>) => req("/settings/risk", { method: "PUT", body: JSON.stringify(risk) }),
  setPair: (symbol: string, on: boolean) =>
    req(`/settings/pairs/${encodeURIComponent(symbol)}`, { method: "PUT", body: JSON.stringify({ on }) }),
  setTelegram: (telegramEnabled: boolean) =>
    req("/settings", { method: "PUT", body: JSON.stringify({ telegramEnabled }) }),
};
