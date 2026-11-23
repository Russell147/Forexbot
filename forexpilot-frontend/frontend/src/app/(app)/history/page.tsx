"use client";
import { HistoryTable } from "@/components/trading/Tables";
import { Card } from "@/components/ui";
import { useBot } from "@/lib/store";

export default function History() {
  const s = useBot();
  return <Card title={`Trade history (${s.trades.length})`}><HistoryTable /></Card>;
}
