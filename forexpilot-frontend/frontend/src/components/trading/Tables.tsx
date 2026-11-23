"use client";
import { TableWrap } from "@/components/ui";
import { f, sg, tone } from "@/lib/format";
import { actions, digits, useBot } from "@/lib/store";

export function PositionsTable({ manual = false }: { manual?: boolean }) {
  const s = useBot();
  return (
    <TableWrap>
      <thead><tr><th>Symbol</th><th>Type</th><th>Lots</th><th>Entry</th><th>SL</th><th>TP</th><th>P/L</th><th>Strategy</th>{manual && <th />}</tr></thead>
      <tbody>
        {s.pos.length === 0 && <tr><td colSpan={9} className="text-slate-500">No open positions</td></tr>}
        {s.pos.map((p) => (
          <tr key={p.id}>
            <td>{p.sym}</td><td className={p.dir === "BUY" ? "text-emerald-600" : "text-red-600"}>{p.dir}</td><td>{p.lot}</td>
            <td>{f(p.entry, digits(p.sym))}</td><td>{f(p.sl, digits(p.sym))}</td><td>{f(p.tp, digits(p.sym))}</td>
            <td className={tone(p.pnl)}>{sg(p.pnl)}</td><td>{p.strat}</td>
            {manual && <td><button className="rounded border border-slate-300 px-2 py-0.5 dark:border-slate-700" onClick={() => actions.close(p.id)}>Close</button></td>}
          </tr>
        ))}
      </tbody>
    </TableWrap>
  );
}
export function HistoryTable({ limit }: { limit?: number }) {
  const s = useBot();
  return (
    <TableWrap>
      <thead><tr><th>Time</th><th>Symbol</th><th>Type</th><th>Lots</th><th>Entry</th><th>Exit</th><th>P/L</th><th>Result</th><th>Strategy</th></tr></thead>
      <tbody>
        {s.trades.slice(0, limit).map((t) => (
          <tr key={t.id}><td>{t.time}</td><td>{t.sym}</td><td>{t.dir}</td><td>{t.lot}</td><td>{f(t.entry, digits(t.sym))}</td><td>{f(t.exit, digits(t.sym))}</td><td className={tone(t.pnl)}>{sg(t.pnl)}</td><td>{t.why}</td><td>{t.strat}</td></tr>
        ))}
      </tbody>
    </TableWrap>
  );
}
