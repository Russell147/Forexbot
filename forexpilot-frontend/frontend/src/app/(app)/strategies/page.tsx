"use client";
import { Card, Switch } from "@/components/ui";
import { actions, useBot } from "@/lib/store";

export default function Strategies() {
  const s = useBot();
  return (
    <>
      <Card title="Strategies" className="mb-3">
        {Object.entries(s.strat).map(([k, v]) => <Switch key={k} title={k} desc={`Timeframes: ${v.tf} · EMA + RSI baseline`} on={v.on} onToggle={() => actions.toggleStrat(k)} />)}
      </Card>
      <Card title="EMA + RSI rules" className="mb-3">
        <p className="text-sm text-slate-500">BUY: fast EMA crosses above slow EMA, RSI confirms bullish momentum, spread within limit, risk limits allow, SL/TP computable, no duplicate position. SELL mirrors this. The bot waits when signals conflict, spread is high, data is missing or the daily loss limit is hit. This is an untested baseline: validate with backtests and demo trading.</p>
      </Card>
      <Card title="AI analysis (Gemini)">
        <p className="text-sm text-slate-500">Supplementary only. The deterministic strategy and risk engine keep final authority over every order. The Gemini key lives on the backend, never in the browser.</p>
      </Card>
    </>
  );
}
