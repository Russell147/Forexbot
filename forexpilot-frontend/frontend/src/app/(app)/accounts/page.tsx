"use client";
import { Card, TableWrap } from "@/components/ui";
import { f } from "@/lib/format";
import { equity, SIMULATOR_MODE, useBot } from "@/lib/store";

export default function Accounts() {
  const s = useBot();
  return (
    <>
      {SIMULATOR_MODE && <div className="mb-3 rounded-lg border border-amber-500 bg-amber-500/10 p-3 text-sm">Simulated account data. Never enter MT5 passwords in the browser; configure them in the trading engine’s environment.</div>}
      <Card title="MT5 account status">
        <TableWrap>
          <thead><tr><th>Account</th><th>Type</th><th>Balance</th><th>Equity</th><th>Status</th></tr></thead>
          <tbody><tr>
            <td>{s.accountLogin ?? (SIMULATOR_MODE ? "DEMO-10482" : "Not connected")}</td>
            <td>{s.accountType ?? (SIMULATOR_MODE ? "demo" : "—")}</td>
            <td>${f(s.bal)}</td><td>${f(equity(s))}</td>
            <td>{SIMULATOR_MODE ? "Simulator" : s.mt5Connected ? "Connected" : s.engineOnline ? "Disconnected" : "Engine offline"}</td>
          </tr></tbody>
        </TableWrap>
      </Card>
    </>
  );
}
