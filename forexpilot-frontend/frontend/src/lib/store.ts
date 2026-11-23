"use client";
import { useSyncExternalStore } from "react";
import type { LogEntry, Position, Risk, Strategy, Trade } from "@/types";
import { api, type ApiAnalytics, type ApiState, type ApiTrade } from "@/services/api";

export const SIMULATOR_MODE = process.env.NEXT_PUBLIC_USE_SIMULATOR !== "false";
export const PAIRS: Record<string, number> = { EURUSD: 1.085, GBPUSD: 1.27, USDJPY: 150, USDCHF: 0.88, AUDUSD: 0.655, USDCAD: 1.36, NZDUSD: 0.6 };
export const pip = (s: string) => (s.includes("JPY") ? 0.01 : 0.0001);
export const digits = (s: string) => (s.includes("JPY") ? 3 : 5);
const rnd = (a: number, b: number) => a + Math.random() * (b - a);

interface Analytics {
  trades: number;
  winRate: number;
  grossProfit: number;
  grossLoss: number;
  net: number;
  profitFactor: number | null;
  byPair: Record<string, number>;
  equityCurve: number[];
}

export type ConnState = "connected" | "disconnected" | "connecting" | "error";

export interface State {
  run: boolean; emg: boolean; bal: number; start: number; peak: number; id: number; tick: number;
  px: Record<string, number>; hist: Record<string, number[]>; spread: Record<string, number>;
  pos: Position[]; trades: Trade[]; eq: number[]; logs: LogEntry[];
  on: Record<string, boolean>; strat: Record<string, Strategy>; tgm: boolean; risk: Risk;
  loading: boolean; error: string | null; engineOnline: boolean; mt5Connected: boolean;
  conn: ConnState; connMessage: string | null; engineAccount: { login?: number; server?: string; type?: string } | null;
  engineLastTick: string | null;
  accountLogin: number | null; accountType: string | null;
  accountEquity: number | null; dayStartEquity: number | null; analytics: Analytics | null;
}

const DEFAULT_RISK: Risk = {
  perTrade: 0.5, maxDaily: 2, maxDD: 5, maxPos: 3, minRR: 2, maxSpread: 1.5,
  closeOnStop: false, session: "All sessions",
};

function initSimulator(): State {
  const keys = Object.keys(PAIRS);
  const s: State = {
    run: false, emg: false, bal: 1000, start: 1000, peak: 1000, id: 1, tick: 0,
    px: { ...PAIRS }, hist: {}, spread: {}, pos: [], trades: [], eq: [], logs: [], tgm: true,
    on: Object.fromEntries(keys.map((k) => [k, true])),
    strat: { Scalping: { on: true, tf: "M1, M5, M15" }, "Day Trading": { on: true, tf: "M15, M30, H1" }, "Swing Trading": { on: false, tf: "H4, D1" } },
    risk: { ...DEFAULT_RISK },
    loading: false, error: null, engineOnline: true, mt5Connected: true,
    conn: "connected", connMessage: null, engineAccount: { login: 10482, server: "Simulator", type: "demo" }, engineLastTick: null,
    accountLogin: 10482, accountType: "demo", accountEquity: null, dayStartEquity: null, analytics: null,
  };
  keys.forEach((k) => { s.hist[k] = [PAIRS[k]]; s.spread[k] = rnd(0.3, 1.2); });
  let b = 1000;
  for (let i = 0; i < 14; i++) {
    const sym = keys[i % 7], win = Math.random() < 0.55, r = 7 * (1 + Math.random()), pnl = win ? r * 1.8 : -r;
    b += pnl;
    s.trades.push({ id: s.id++, sym, dir: i % 2 ? "SELL" : "BUY", lot: 0.01, entry: PAIRS[sym], exit: PAIRS[sym], sl: 0, tp: 0, slp: 0, rr: 2, pnl, why: win ? "Take-profit" : "Stop-loss", strat: "EMA_RSI · " + (i % 2 ? "Day Trading" : "Scalping"), time: new Date(Date.now() - (15 - i) * 36e5).toLocaleString(), day: false });
  }
  s.bal = s.start = s.peak = b;
  for (let i = 0; i < 60; i++) s.eq.push(b + Math.sin(i / 6) * 3);
  return s;
}

function initBackend(): State {
  return {
    run: false, emg: false, bal: 0, start: 0, peak: 0, id: 1, tick: 0,
    px: {}, hist: {}, spread: {}, pos: [], trades: [], eq: [], logs: [],
    on: {}, strat: {}, tgm: false, risk: { ...DEFAULT_RISK },
    loading: true, error: null, engineOnline: false, mt5Connected: false,
    conn: "connecting", connMessage: "Connecting to the trading engine...", engineAccount: null, engineLastTick: null,
    accountLogin: null, accountType: null, accountEquity: null, dayStartEquity: null, analytics: null,
  };
}

let S: State = SIMULATOR_MODE ? initSimulator() : initBackend();
const subs = new Set<() => void>();
const emit = () => { S = { ...S }; subs.forEach((fn) => fn()); };
const log = (m: string) => { S.logs = [{ t: new Date().toLocaleTimeString(), m }, ...S.logs].slice(0, 80); };

function toPosition(t: ApiTrade): Position {
  return { id: t.id, sym: t.sym, dir: t.dir, entry: t.entry, sl: t.sl, tp: t.tp, lot: t.lot, strat: t.strat, pnl: t.pnl, slp: 0, rr: 0 };
}

function toTrade(t: ApiTrade): Trade {
  const time = t.time ?? "";
  const today = time ? new Date(time).toDateString() === new Date().toDateString() : false;
  return { ...toPosition(t), exit: t.exit ?? 0, why: t.why ?? "", time, day: today };
}

function applyBackendState(state: ApiState, analytics: ApiAnalytics): void {
  const engine = state.engine;
  const conn: ConnState = engine?.state ?? (
    state.engineOnline && state.mt5Connected ? "connected" : state.engineOnline ? "error" : "disconnected"
  );
  const connMessage = engine?.message ?? (
    conn === "connected" ? "MT5 connected and trading engine is online"
      : conn === "error" ? "MT5 connection error in the trading engine"
        : conn === "connecting" ? "Connecting to the trading engine..."
          : "Trading engine is offline. Start trading-engine/main.py on the MT5 machine first."
  );
  S = {
    ...S,
    run: state.run,
    emg: state.emg,
    bal: state.bal,
    start: state.dayStartEquity,
    peak: state.peak,
    pos: state.pos.map(toPosition),
    trades: state.trades.map(toTrade),
    eq: analytics.equityCurve.map((point) => point.equity),
    logs: state.logs.map((entry) => ({ t: entry.t ?? "", m: entry.m })),
    on: state.on,
    strat: state.strat,
    tgm: state.tgm,
    risk: { ...state.risk, ...pendingRisk },
    loading: false,
    error: null,
    engineOnline: state.engineOnline,
    mt5Connected: state.mt5Connected,
    conn,
    connMessage,
    engineAccount: engine?.account ?? null,
    engineLastTick: engine?.last_tick ?? null,
    accountLogin: state.account.login,
    accountType: state.account.type,
    accountEquity: state.equity,
    dayStartEquity: state.dayStartEquity,
    analytics: {
      trades: analytics.trades,
      winRate: analytics.winRate,
      grossProfit: analytics.grossProfit,
      grossLoss: analytics.grossLoss,
      net: analytics.net,
      profitFactor: analytics.profitFactor,
      byPair: analytics.byPair,
      equityCurve: analytics.equityCurve.map((point) => point.equity),
    },
  };
  emit();
}

let pendingRisk: Partial<Risk> = {};

async function refreshBackend(): Promise<void> {
  const [state, analytics] = await Promise.all([api.state(), api.analytics()]);
  applyBackendState(state, analytics);
}

async function backendAction(action: () => Promise<unknown>): Promise<void> {
  S.error = null;
  emit();
  try {
    await action();
    await refreshBackend();
  } catch (error) {
    S.error = error instanceof Error ? error.message : String(error);
    emit();
  }
}

export const equity = (s: State = S) => s.accountEquity ?? s.bal + s.pos.reduce((a, p) => a + p.pnl, 0);
export const dayPL = (s: State = S) => s.dayStartEquity === null
  ? s.trades.filter((t) => t.day).reduce((a, t) => a + t.pnl, 0) + s.pos.reduce((a, p) => a + p.pnl, 0)
  : equity(s) - s.dayStartEquity;

export function stats(s: State) {
  if (s.analytics) {
    return {
      n: s.analytics.trades, wr: s.analytics.winRate, gp: s.analytics.grossProfit,
      gl: s.analytics.grossLoss, pf: s.analytics.profitFactor ?? 0, net: s.analytics.net,
      dd: s.peak > 0 ? ((s.peak - equity(s)) / s.peak) * 100 : 0,
    };
  }
  const w = s.trades.filter((t) => t.pnl > 0), l = s.trades.filter((t) => t.pnl <= 0);
  const gp = w.reduce((a, t) => a + t.pnl, 0), gl = -l.reduce((a, t) => a + t.pnl, 0);
  return { n: s.trades.length, wr: s.trades.length ? (w.length / s.trades.length) * 100 : 0, gp, gl, pf: gl ? gp / gl : 0, net: gp - gl, dd: s.peak ? ((s.peak - equity(s)) / s.peak) * 100 : 0 };
}

function openPos(sym: string, dir: "BUY" | "SELL", strat: string) {
  const R = S.risk, slp = Math.round(rnd(12, 28)), rr = Math.max(R.minRR, 2), e = S.px[sym], pp = pip(sym), d = dir === "BUY" ? 1 : -1;
  const lot = Math.max(0.01, Math.floor(((equity() * R.perTrade) / 100 / (slp * 10)) * 100) / 100);
  S.pos.push({ id: S.id++, sym, dir, entry: e, sl: e - d * slp * pp, tp: e + d * slp * rr * pp, lot, strat: "EMA_RSI · " + strat, pnl: 0, slp, rr });
  log(`Opened ${dir} ${sym} ${lot} lot · SL ${slp}p · R:R 1:${rr}`);
}
function closePos(p: Position, why: string) {
  S.pos = S.pos.filter((x) => x.id !== p.id);
  S.bal += p.pnl;
  S.trades = [{ ...p, exit: S.px[p.sym], why, time: new Date().toLocaleString(), day: true }, ...S.trades];
  log(`Closed ${p.sym} ${p.pnl >= 0 ? "+" : "−"}$${Math.abs(p.pnl).toFixed(2)} (${why})`);
}
function signal() {
  const R = S.risk, act = Object.keys(S.strat).filter((k) => S.strat[k].on), syms = Object.keys(PAIRS).filter((k) => S.on[k]);
  if (!act.length || !syms.length) return;
  const sym = syms[Math.floor(Math.random() * syms.length)], st = act[Math.floor(Math.random() * act.length)];
  if (S.pos.length >= R.maxPos || S.pos.some((p) => p.sym === sym)) return;
  if (S.spread[sym] > R.maxSpread) { log(`WAIT ${sym}: spread above limit`); return; }
  if (Math.random() < 0.45) { log(`WAIT ${sym}: EMA/RSI signals conflict`); return; }
  openPos(sym, Math.random() < 0.5 ? "BUY" : "SELL", st);
}
function step() {
  S.tick++;
  for (const k of Object.keys(PAIRS)) {
    S.px[k] = Math.max(0, S.px[k] + pip(k) * rnd(-2.2, 2.2));
    S.hist[k] = [...S.hist[k], S.px[k]].slice(-50);
    S.spread[k] = Math.max(0.2, S.spread[k] + rnd(-0.2, 0.2));
  }
  for (const p of [...S.pos]) {
    const d = p.dir === "BUY" ? 1 : -1, c = S.px[p.sym];
    p.pnl = (d * (c - p.entry)) / pip(p.sym) * p.lot * 10;
    if (d * (c - p.sl) <= 0) { p.pnl = -p.slp * p.lot * 10; closePos(p, "Stop-loss"); }
    else if (d * (c - p.tp) >= 0) { p.pnl = p.slp * p.rr * p.lot * 10; closePos(p, "Take-profit"); }
  }
  const eq = equity();
  S.peak = Math.max(S.peak, eq);
  S.eq = [...S.eq, eq].slice(-200);
  if (S.run && !S.emg) {
    if ((-dayPL() / S.start) * 100 >= S.risk.maxDaily) { S.run = false; log("Daily loss limit reached — trading halted"); }
    else if (((S.peak - eq) / S.peak) * 100 >= S.risk.maxDD) { S.run = false; log("Max drawdown reached — trading halted"); }
    else if (S.tick % 5 === 0) signal();
  }
  emit();
}

let simulatorTimer: ReturnType<typeof setInterval> | undefined;
let riskTimer: ReturnType<typeof setTimeout> | undefined;

export const startEngine = (): (() => void) => {
  if (SIMULATOR_MODE) {
    if (!simulatorTimer) simulatorTimer = setInterval(step, 1000);
    return () => {
      if (simulatorTimer) clearInterval(simulatorTimer);
      simulatorTimer = undefined;
    };
  }

  let stopped = false;
  let inFlight = false;
  let timeout: ReturnType<typeof setTimeout>;
  const poll = async () => {
    if (stopped || inFlight) return;
    inFlight = true;
    try {
      await refreshBackend();
    } catch (error) {
      S.loading = false;
      S.conn = "disconnected";
      S.connMessage = "Cannot reach the dashboard API. Retrying automatically...";
      S.engineOnline = false;
      S.mt5Connected = false;
      S.error = error instanceof Error ? error.message : String(error);
      emit();
    } finally {
      inFlight = false;
      if (!stopped) timeout = setTimeout(poll, 3000);
    }
  };
  void poll();
  return () => {
    stopped = true;
    clearTimeout(timeout);
  };
};

export const actions = {
  async refresh() {
    S.error = null;
    S.conn = "connecting";
    S.connMessage = "Connecting to the trading engine...";
    emit();
    try {
      await refreshBackend();
    } catch (error) {
      S.loading = false;
      S.conn = "disconnected";
      S.connMessage = "Cannot reach the dashboard API. Retrying automatically...";
      S.error = error instanceof Error ? error.message : String(error);
      emit();
    }
  },
  async toggleBot() {
    if (SIMULATOR_MODE) {
      if (S.emg) { S.emg = false; log("Emergency stop cleared"); }
      else { S.run = !S.run; log(S.run ? "Bot started · MT5 connected" : "Bot stopped"); }
      emit();
      return;
    }
    await backendAction(() => S.run || S.emg ? api.botStop() : api.botStart());
  },
  async emergency() {
    if (SIMULATOR_MODE) {
      S.emg = true; S.run = false; log("EMERGENCY STOP: new trades blocked");
      if (S.risk.closeOnStop) [...S.pos].forEach((p) => closePos(p, "Emergency close"));
      emit();
      return;
    }
    await backendAction(() => api.emergencyStop(S.risk.closeOnStop));
  },
  async close(id: number) {
    if (!SIMULATOR_MODE) {
      S.error = "Manual position closing is not available in the backend API.";
      emit();
      return;
    }
    const p = S.pos.find((x) => x.id === id);
    if (p) closePos(p, "Manual close");
    emit();
  },
  async toggleStrat(k: string) {
    const on = !S.strat[k].on;
    if (SIMULATOR_MODE) { S.strat[k].on = on; emit(); return; }
    await backendAction(() => api.setStrategy(k, on));
  },
  async togglePair(k: string) {
    const on = !S.on[k];
    if (SIMULATOR_MODE) { S.on[k] = on; emit(); return; }
    await backendAction(() => api.setPair(k, on));
  },
  async toggleTelegram() {
    const enabled = !S.tgm;
    if (SIMULATOR_MODE) { S.tgm = enabled; emit(); return; }
    await backendAction(() => api.setTelegram(enabled));
  },
  setRisk<K extends keyof Risk>(k: K, v: Risk[K]) {
    if (SIMULATOR_MODE) {
      S.risk = { ...S.risk, [k]: v }; log("Risk setting updated: " + k); emit();
      return;
    }
    S.risk = { ...S.risk, [k]: v };
    pendingRisk[k] = v;
    emit();
    if (riskTimer) clearTimeout(riskTimer);
    riskTimer = setTimeout(() => {
      const update = pendingRisk;
      pendingRisk = {};
      void backendAction(() => api.setRisk(update));
    }, 500);
  },
};

export function useBot(): State {
  return useSyncExternalStore((cb) => { subs.add(cb); return () => { subs.delete(cb); }; }, () => S, () => S);
}
