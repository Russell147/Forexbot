"use client";
import { Line } from "@/components/charts/Line";
import { HistoryTable, PositionsTable } from "@/components/trading/Tables";
import { Card, LogList, Stat, StatGrid, TableWrap } from "@/components/ui";
import { f, sg, tone } from "@/lib/format";
import { dayPL, equity, SIMULATOR_MODE, stats, useBot } from "@/lib/store";
import type { ApiAnalysis } from "@/services/api";

const sigClass = (s: string) => s === "BUY" ? "text-emerald-600" : s === "SELL" ? "text-red-600" : "text-slate-500";
const trendClass = (t: string) => t === "BULLISH" ? "text-emerald-600" : t === "BEARISH" ? "text-red-600" : "text-slate-500";
const fmt = (n: number, d = 5) => Number.isFinite(n) ? n.toFixed(d) : "—";

function AnalysisRows({ analysis }: { analysis: Record<string, ApiAnalysis> }) {
  const rows = Object.values(analysis);
  if (!rows.length) return <p className="text-xs text-slate-500">No analysis yet — waiting for the engine to read closed candles.</p>;
  return (
    <TableWrap>
      <thead><tr>
        <th>Pair</th><th>Signal</th><th>Price</th><th>EMA 20/50</th><th>RSI 14</th><th>MACD hist</th><th>Trend</th><th>Candle</th><th>Support / Resistance</th><th>Strategy · TF</th>
      </tr></thead>
      <tbody>
        {rows.map((a) => (
          <tr key={a.symbol}>
            <td className="font-semibold">{a.symbol}</td>
            <td className={`font-semibold ${sigClass(a.signal)}`}>{a.signal}</td>
            <td>{fmt(a.price)}</td>
            <td>{fmt(a.ema20)} / {fmt(a.ema50)}</td>
            <td>{fmt(a.rsi, 1)}</td>
            <td className={a.macdHist > 0 ? "text-emerald-600" : a.macdHist < 0 ? "text-red-600" : ""}>{fmt(a.macdHist, 6)}</td>
            <td className={trendClass(a.trend)}>{a.trend}</td>
            <td>{a.candle}</td>
            <td>{fmt(a.support)} / {fmt(a.resistance)}</td>
            <td className="text-xs text-slate-500">{a.strategy} · {a.timeframe}</td>
          </tr>
        ))}
      </tbody>
    </TableWrap>
  );
}

export default function Dashboard() {
  const s = useBot(), st = stats(s), d = dayPL(s);
  return (
    <>
      <StatGrid>
        <Stat label="Account balance" value={"$" + f(s.bal)} />
        <Stat label="Account equity" value={"$" + f(equity(s))} />
        <Stat label="Today’s P/L" value={sg(d)} className={tone(d)} />
        <Stat label="Total profit" value={"+$" + f(st.gp)} className="text-emerald-600" />
        <Stat label="Total losses" value={"−$" + f(st.gl)} className="text-red-600" />
        <Stat label="Win rate" value={f(st.wr, 1) + "%"} />
        <Stat label="Active trades" value={`${s.pos.length} / ${s.risk.maxPos}`} />
      </StatGrid>
      <Card title="MT5 connection" className="mb-3">
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          <span>Status: <strong>{SIMULATOR_MODE ? "Simulator" : s.conn === "connected" ? "Connected" : s.conn === "connecting" ? "Connecting" : s.conn === "error" ? "Error" : "Disconnected"}</strong></span>
          <span>Account: <strong>{s.engineAccount?.login ?? s.accountLogin ?? "—"}</strong></span>
          <span>Server: <strong>{s.engineAccount?.server ?? "—"}</strong></span>
          <span>Type: <strong>{s.engineAccount?.type ?? s.accountType ?? "—"}</strong></span>
          <span>Bot: <strong>{s.liveBlocked ? "BLOCKED (live account)" : s.run ? "RUNNING" : "STOPPED"}</strong></span>
          <span>Last engine tick: <strong>{s.engineLastTick ? new Date(s.engineLastTick).toLocaleTimeString() : "—"}</strong></span>
        </div>
        {s.connMessage && <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">{s.connMessage}</div>}
      </Card>
      <Card title="Technical analysis (latest closed candle · read-only)" className="mb-3">
        <AnalysisRows analysis={s.analysis} />
        <p className="mt-2 text-xs text-slate-400">Signals are EMA-cross triggers confirmed by RSI, MACD, trend and candlestick pattern. Support/resistance are recent swing levels. HOLD means no confirmed trade.</p>
      </Card>
      <div className="mb-3 grid gap-3 lg:grid-cols-3">
        <Card title="Equity curve (live)" className="lg:col-span-2"><Line data={s.eq} /></Card>
        <Card title="Engine activity"><LogList items={s.logs} /></Card>
      </div>
      <Card title="Open positions" className="mb-3"><PositionsTable /></Card>
      <Card title="Recent trades" className="mb-3"><HistoryTable limit={6} /></Card>
      <div className="mb-3 grid gap-3 lg:grid-cols-2">
        <Card title="Recent signals">
          {s.signals.length === 0 ? <p className="text-xs text-slate-500">No signals recorded yet.</p> : (
            <TableWrap>
              <thead><tr><th>Time</th><th>Pair</th><th>Dir</th><th>Strategy · TF</th><th>Status</th><th>Reason</th></tr></thead>
              <tbody>
                {s.signals.slice(0, 12).map((g, i) => (
                  <tr key={i}>
                    <td className="text-xs">{g.time ? new Date(g.time).toLocaleTimeString() : "—"}</td>
                    <td>{g.symbol}</td>
                    <td className={sigClass(g.direction)}>{g.direction || "HOLD"}</td>
                    <td className="text-xs text-slate-500">{g.strategy} · {g.timeframe}</td>
                    <td className={g.status === "EXECUTED" ? "text-emerald-600" : "text-amber-600"}>{g.status}</td>
                    <td className="max-w-xs truncate text-xs" title={g.reason}>{g.reason}</td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          )}
        </Card>
        <Card title="Active strategies">
          <div className="flex flex-wrap gap-2">
            {Object.entries(s.strat).map(([k, v]) => <span key={k} className="rounded-full border border-slate-200 px-3 py-0.5 text-xs dark:border-slate-700">{v.on ? "● " : "○ "}{k}</span>)}
          </div>
          <p className="mt-3 text-xs text-slate-500">Lots: {s.risk.lotMode === "fixed" ? `fixed ${s.risk.fixedLot}` : `risk-based ${s.risk.perTrade}%`} · cap {s.risk.maxLotSize} · max {s.risk.maxPos} positions · max daily loss {s.risk.maxDaily}% · max spread {s.risk.maxSpread}p · max {s.risk.maxDailyTrades} trades/day · stop after {s.risk.maxConsecutiveLosses} losses.</p>
        </Card>
      </div>
    </>
  );
}
