"use client";
import { Line } from "@/components/charts/Line";
import { HistoryTable, PositionsTable } from "@/components/trading/Tables";
import { Card, LogList, Stat, StatGrid } from "@/components/ui";
import { f, sg, tone } from "@/lib/format";
import { dayPL, equity, SIMULATOR_MODE, stats, useBot } from "@/lib/store";

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
          <span>Last engine tick: <strong>{s.engineLastTick ? new Date(s.engineLastTick).toLocaleTimeString() : "—"}</strong></span>
        </div>
        {s.connMessage && <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">{s.connMessage}</div>}
      </Card>
      <div className="mb-3 grid gap-3 lg:grid-cols-3">
        <Card title="Equity curve (live)" className="lg:col-span-2"><Line data={s.eq} /></Card>
        <Card title="Engine activity"><LogList items={s.logs} /></Card>
      </div>
      <Card title="Open positions" className="mb-3"><PositionsTable /></Card>
      <Card title="Recent trades" className="mb-3"><HistoryTable limit={6} /></Card>
      <Card title="Active strategies">
        <div className="flex flex-wrap gap-2">
          {Object.entries(s.strat).map(([k, v]) => <span key={k} className="rounded-full border border-slate-200 px-3 py-0.5 text-xs dark:border-slate-700">{v.on ? "● " : "○ "}{k}</span>)}
        </div>
      </Card>
    </>
  );
}
