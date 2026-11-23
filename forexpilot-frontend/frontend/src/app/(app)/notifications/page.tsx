"use client";
import { Card, LogList } from "@/components/ui";
import { useBot } from "@/lib/store";

export default function Notifications() {
  const s = useBot();
  return <Card title="Alerts and Telegram feed"><LogList items={s.logs} /></Card>;
}
