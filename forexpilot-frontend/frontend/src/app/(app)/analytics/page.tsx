"use client";
import { Line } from "@/components/charts/Line";
import { Card, Stat, StatGrid, TableWrap } from "@/components/ui";
import { f, sg, tone } from "@/lib/format";
import { stats, useBot } from "@/lib/store";

export default function Analytics() {
  const s = useBot(), st = stats(s);
  let run = 0;
  const cum = s.analytics?.equityCurve ?? [...s.trades].reverse().map((t) => (run += t.pnl));
  const by: Record<string, number> = {};
  s.trades.forEach((t) => { by[t.sym] = (by[t.sym] ?? 0) + t.pnl; });
  const byPair = s.analytics?.byPair ?? by;
  return (
    <>
      <StatGrid>
        <Stat label="Net profit" value={sg(st.net)} className={tone(st.net)} />
        <Stat label="Profit factor" value={f(st.pf)} />
        <Stat label="Trades" value={st.n} />
        <Stat label="Win rate" value={f(st.wr, 1) + "%"} />
        <Stat label="Current drawdown" value={f(st.dd) + "%"} />
      </StatGrid>
      <Card title={s.analytics ? "Account equity" : "Cumulative P/L"} className="mb-3"><Line data={cum} height={180} className="stroke-emerald-500" /></Card>
      <Card title="P/L by pair">
        <TableWrap><tbody>{Object.entries(byPair).map(([k, v]) => <tr key={k}><td>{k}</td><td className={tone(v)}>{sg(v)}</td></tr>)}</tbody></TableWrap>
      </Card>
    </>
  );
}
