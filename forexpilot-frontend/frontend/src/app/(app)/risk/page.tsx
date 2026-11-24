"use client";
import { Card, Switch } from "@/components/ui";
import type { Risk } from "@/types";
import { actions, useBot } from "@/lib/store";

type NumKey = { [K in keyof Risk]-?: NonNullable<Risk[K]> extends number ? K : never }[keyof Risk];
const FIELDS: [NumKey, string, number, number, number][] = [
  ["perTrade", "Risk per trade (%)", 0.1, 0.1, 5], ["maxDaily", "Maximum daily loss (%)", 0.1, 0.1, 20], ["maxDD", "Maximum drawdown (%)", 0.1, 0.1, 50],
  ["maxPos", "Maximum open positions", 1, 1, 20], ["minRR", "Minimum risk/reward (1:x)", 0.1, 1, 10], ["maxSpread", "Maximum spread (pips)", 0.1, 0.1, 20],
  ["maxDailyTrades", "Maximum trades per day", 1, 1, 100], ["maxConsecutiveLosses", "Stop after consecutive losses", 1, 1, 10],
];
const input = "w-full max-w-xs rounded-lg border border-slate-300 bg-slate-50 px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950";

export default function RiskPage() {
  const { risk } = useBot();
  const num = (k: NumKey, label: string, step: number, min: number, max: number) => (
    <label key={k} className="mb-3 block">
      <span className="mb-1 block text-xs text-slate-500">{label}</span>
      <input className={input} type="number" min={min} max={max} step={step} value={risk[k]} onChange={(e) => actions.setRisk(k, Math.max(min, Math.min(max, parseFloat(e.target.value) || min)))} />
    </label>
  );
  return (
    <Card title="Risk management (mandatory)">
      {FIELDS.map(([k, label, step, min, max]) => num(k, label, step, min, max))}
      <div className="mb-4 border-t border-slate-200 pt-3 dark:border-slate-700">
        <div className="mb-2 text-xs font-semibold">Position sizing</div>
        <label className="mb-3 block">
          <span className="mb-1 block text-xs text-slate-500">Lot sizing mode</span>
          <select className={input} value={risk.lotMode} onChange={(e) => actions.setRisk("lotMode", e.target.value as Risk["lotMode"])}>
            <option value="risk">Risk-based (risk % ÷ stop distance)</option>
            <option value="fixed">Fixed lot (ignore risk %)</option>
          </select>
        </label>
        {num("fixedLot", "Fixed lot size (used when mode = fixed)", 0.01, 0.01, 100)}
        {num("maxLotSize", "Maximum lot size per trade (applies in both modes)", 0.01, 0.01, 100)}
        <p className="text-xs text-slate-500">Default cap is 0.10 lots. In risk mode the engine computes a size from your risk % and stop distance, then caps it here. Set the cap slightly above your broker minimum to trade small.</p>
      </div>
      <div className="mb-4 border-t border-slate-200 pt-3 dark:border-slate-700">
        <div className="mb-2 text-xs font-semibold">Trade exits</div>
        {num("breakEvenAfterR", "Move SL to break-even after (1R = initial stop distance)", 0.1, 0, 10)}
        {num("partialTpR", "Partial close at (R, 0 = off)", 0.1, 0, 10)}
        {num("partialTpPct", "Partial close size (% of position)", 5, 0, 100)}
        {num("maxHoldHours", "Maximum hold time in hours (0 = off)", 1, 0, 720)}
        <p className="text-xs text-slate-500">Break-even and partial TP use the initial stop to define 1R. Broker stop-distance rules are respected when moving a stop.</p>
      </div>
      <div className="mb-4 border-t border-slate-200 pt-3 dark:border-slate-700">
        <div className="mb-2 text-xs font-semibold">Correlation / exposure</div>
        {num("maxCurrencyExposure", "Max open positions touching one currency (0 = off)", 1, 0, 10)}
        <p className="text-xs text-slate-500">Blocks a new trade if it would push any currency past the limit, so three USD pairs cannot open at once. Default is 2.</p>
      </div>
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
