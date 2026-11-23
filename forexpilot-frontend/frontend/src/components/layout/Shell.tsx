"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { Btn } from "@/components/ui";
import { useMounted } from "@/hooks/useMounted";
import { actions, SIMULATOR_MODE, startEngine, useBot } from "@/lib/store";
import { api } from "@/services/api";

export const NAV = [
  ["/dashboard", "Dashboard"], ["/trading", "Live Trading"], ["/strategies", "Strategies"], ["/history", "Trade History"],
  ["/analytics", "Analytics"], ["/risk", "Risk Management"], ["/accounts", "MT5 Accounts"], ["/notifications", "Notifications"], ["/settings", "Settings"],
] as const;

const Dot = ({ c }: { c: string }) => <span className={`mr-1.5 inline-block h-2 w-2 rounded-full ${c}`} />;

const CONN_STYLE = {
  connected: { dot: "bg-emerald-500", label: "Engine connected" },
  connecting: { dot: "bg-amber-500 animate-pulse", label: "Connecting..." },
  error: { dot: "bg-red-500", label: "Engine error" },
  disconnected: { dot: "bg-slate-400", label: "Engine offline" },
} as const;

export default function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const mounted = useMounted();
  const s = useBot();
  const [authReady, setAuthReady] = useState(SIMULATOR_MODE);
  const [authError, setAuthError] = useState<string | null>(null);
  useEffect(() => {
    if (SIMULATOR_MODE) return startEngine();
    let active = true;
    let stopSync = () => {};
    void api.me().then(() => {
      if (!active) return;
      setAuthReady(true);
      stopSync = startEngine();
    }).catch(() => {
      if (active) router.replace("/login");
    });
    return () => {
      active = false;
      stopSync();
    };
  }, [router]);
  if (!mounted || !authReady) return <div className="min-h-screen" />;
  const title = NAV.find(([h]) => h === path)?.[1] ?? "ForexPilot AI";
  const logout = async () => {
    try {
      await api.logout();
      router.replace("/login");
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : String(error));
    }
  };
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <nav className="flex shrink-0 gap-1 overflow-x-auto border-b border-slate-200 bg-white p-2 md:sticky md:top-0 md:h-screen md:w-52 md:flex-col md:border-b-0 md:border-r md:p-3 dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-4 hidden px-2 text-base font-bold md:block">Forex<span className="text-brand">Pilot</span> AI</div>
        {NAV.map(([href, label]) => (
          <Link key={href} href={href} className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm ${path === href ? "bg-slate-100 font-medium dark:bg-slate-800" : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"}`}>{label}</Link>
        ))}
      </nav>
      <main className="min-w-0 flex-1 p-4 md:p-5">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <h1 className="flex-1 text-xl font-semibold">{title}</h1>
          <span className="rounded-full border border-slate-200 bg-white px-3 py-0.5 text-xs dark:border-slate-800 dark:bg-slate-900"><Dot c={s.emg ? "bg-red-500" : s.run ? "bg-emerald-500" : "bg-slate-400"} />{s.emg ? "Emergency stop" : s.run ? "Bot running" : "Bot stopped"}</span>
          <span
            title={s.connMessage ?? undefined}
            className="rounded-full border border-slate-200 bg-white px-3 py-0.5 text-xs dark:border-slate-800 dark:bg-slate-900"
          >
            <Dot c={SIMULATOR_MODE ? "bg-emerald-500" : CONN_STYLE[s.conn].dot} />
            {SIMULATOR_MODE ? "Simulator" : CONN_STYLE[s.conn].label}
          </span>
          <Btn variant={s.run ? "default" : "primary"} onClick={actions.toggleBot}>{s.emg ? "Reset emergency" : s.run ? "Stop bot" : "Start bot"}</Btn>
          <Btn variant="danger" onClick={actions.emergency}>Emergency stop</Btn>
          {!SIMULATOR_MODE && <Btn onClick={logout}>Sign out</Btn>}
        </div>
        {(authError || s.error || (!SIMULATOR_MODE && s.conn !== "connected")) && (
          <div role="alert" className="mb-3 flex flex-wrap items-center gap-2 rounded-lg border border-red-500 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300">
            <span className="flex-1">{authError ?? s.error ?? s.connMessage}</span>
            {!SIMULATOR_MODE && s.conn !== "connected" && <Btn onClick={actions.refresh}>Retry</Btn>}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
