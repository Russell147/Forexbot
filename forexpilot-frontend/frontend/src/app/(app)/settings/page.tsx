"use client";
import { Card, Switch } from "@/components/ui";
import { actions, useBot } from "@/lib/store";

export default function Settings() {
  const s = useBot();
  return (
    <>
      <Card title="Monitored pairs" className="mb-3">
        {Object.keys(s.on).map((k) => <Switch key={k} title={k} desc="Include in market scan" on={s.on[k]} onToggle={() => actions.togglePair(k)} />)}
      </Card>
      <Card title="Notifications">
        <Switch title="Telegram notifications" desc="Bot started, trades opened/closed, limit breaches, connection loss" on={s.tgm} onToggle={actions.toggleTelegram} />
      </Card>
    </>
  );
}
