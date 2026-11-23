"use client";
import { Line } from "@/components/charts/Line";
import { PositionsTable } from "@/components/trading/Tables";
import { Card, LogList, TableWrap } from "@/components/ui";
import { f } from "@/lib/format";
import { PAIRS, SIMULATOR_MODE, digits, useBot } from "@/lib/store";

export default function Trading() {
  const s = useBot();
  return (
    <>
      {SIMULATOR_MODE ? (
        <Card title="Market watch" className="mb-3">
          <TableWrap>
            <thead><tr><th>Pair</th><th>Price</th><th>Spread</th><th>Trend</th><th>Monitoring</th></tr></thead>
            <tbody>
              {Object.keys(PAIRS).map((k) => (
                <tr key={k}>
                  <td>{k}</td><td>{f(s.px[k], digits(k))}</td>
                  <td className={s.spread[k] > s.risk.maxSpread ? "text-red-600" : ""}>{f(s.spread[k], 1)}p</td>
                  <td className="w-28"><Line data={s.hist[k]} height={24} strokeWidth={1.5} /></td>
                  <td>{s.on[k] ? "Yes" : "Paused"}</td>
                </tr>
              ))}
            </tbody>
          </TableWrap>
        </Card>
      ) : (
        <Card title="Monitored pairs" className="mb-3">
          <p className="mb-2 text-sm text-slate-500">The API does not currently provide live quote or spread data.</p>
          <TableWrap>
            <thead><tr><th>Pair</th><th>Monitoring</th></tr></thead>
            <tbody>{Object.entries(s.on).map(([symbol, enabled]) => <tr key={symbol}><td>{symbol}</td><td>{enabled ? "Yes" : "Paused"}</td></tr>)}</tbody>
          </TableWrap>
        </Card>
      )}
      <Card title="Live positions" className="mb-3"><PositionsTable manual={SIMULATOR_MODE} /></Card>
      {!SIMULATOR_MODE && <p className="mb-3 text-xs text-slate-500">Manual position closing is not available in the backend API yet.</p>}
      <Card title="Decision log"><LogList items={s.logs} /></Card>
    </>
  );
}
