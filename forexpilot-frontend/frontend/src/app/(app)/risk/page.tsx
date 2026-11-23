"use client";
import { Card, Switch } from "@/components/ui";
import type { Risk } from "@/types";
import { actions, useBot } from "@/lib/store";

type NumKey = { [K in keyof Risk]: Risk[K] extends number ? K : never }[keyof Risk];
const FIELDS: [NumKey, string, number, number, number][] = [
  ["perTrade", "Risk per trade (%)", 0.1, 0.1, 5], ["maxDaily", "Maximum daily loss (%)", 0.1, 0.1, 20], ["maxDD", "Maximum drawdown (%)", 0.1, 0.1, 50],
  ["maxPos", "Maximum open positions", 1, 1, 20], ["minRR", "Minimum risk/reward (1:x)", 0.1, 1, 10], ["maxSpread", "Maximum spread (pips)", 0.1, 0.1, 20],
];
const input = "w-full max-w-xs rounded-lg border border-slate-300 bg-slate-50 px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950";

export default function RiskPage() {
  const { risk } = useBot();
  return (
    <Card title="Risk management (mandatory)">
      {FIELDS.map(([k, label, step, min, max]) => (
        <label key={k} className="mb-3 block">
          <span className="mb-1 block text-xs text-slate-500">{label}</span>
          <input className={input} type="number" min={min} max={max} step={step} value={risk[k]} onChange={(e) => actions.setRisk(k, Math.max(min, Math.min(max, parseFloat(e.target.value) || min)))} />
        </label>
      ))}
      <label className="mb-3 block">
        <span className="mb-1 block text-xs text-slate-500">Trading session</span>
        <select className={input} value={risk.session} onChange={(e) => actions.setRisk("session", e.target.value)}>
          {["All sessions", "London", "New York", "London + New York"].map((o) => <option key={o}>{o}</option>)}
        </select>
      </label>
      <Switch title="Close positions on emergency stop" desc="Off: emergency stop only blocks new trades" on={risk.closeOnStop} onToggle={() => actions.setRisk("closeOnStop", !risk.closeOnStop)} />
      <p className="mt-3 text-xs text-slate-500">Stop-loss and take-profit are always mandatory. These are conservative test values, not safety or profit guarantees; validate against your broker’s conditions.</p>
    </Card>
  );
}
