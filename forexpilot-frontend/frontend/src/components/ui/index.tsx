import type { ReactNode } from "react";
export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 ${className}`}>
      {title && <h3 className="mb-3 text-sm font-semibold">{title}</h3>}
      {children}
    </section>
  );
}
export function Stat({ label, value, className = "" }: { label: string; value: ReactNode; className?: string }) {
  return (
    <Card>
      <div className="text-xs text-slate-500 dark:text-slate-400">{label}</div>
      <div className={`text-2xl font-semibold ${className}`}>{value}</div>
    </Card>
  );
}
export const StatGrid = ({ children }: { children: ReactNode }) => <div className="mb-3 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">{children}</div>;
export function Btn({ variant = "default", className = "", ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default" | "primary" | "danger" }) {
  const v = { default: "border-slate-300 dark:border-slate-700", primary: "border-brand bg-brand text-white", danger: "border-red-600 bg-red-600 text-white" }[variant];
  return <button {...p} className={`rounded-lg border px-3 py-1.5 text-sm ${v} ${className}`} />;
}
export function Switch({ title, desc, on, onToggle }: { title: string; desc?: string; on: boolean; onToggle: () => void }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-200 py-3 last:border-0 dark:border-slate-800">
      <div><div className="font-medium">{title}</div>{desc && <div className="text-xs text-slate-500 dark:text-slate-400">{desc}</div>}</div>
      <Btn variant={on ? "primary" : "default"} onClick={onToggle}>{on ? "Enabled" : "Disabled"}</Btn>
    </div>
  );
}
export const TableWrap = ({ children }: { children: ReactNode }) => (
  <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm [&_td]:whitespace-nowrap [&_td]:border-b [&_td]:border-slate-200 [&_td]:px-2 [&_td]:py-2 [&_th]:px-2 [&_th]:py-2 [&_th]:text-xs [&_th]:font-medium [&_th]:text-slate-500 dark:[&_td]:border-slate-800">{children}</table></div>
);
export const LogList = ({ items }: { items: { t: string; m: string }[] }) => (
  <div className="max-h-72 overflow-auto text-sm">
    {items.length ? items.map((l, i) => <div key={i} className="border-b border-slate-200 py-1.5 dark:border-slate-800"><span className="text-xs text-slate-500">{l.t}</span> {l.m}</div>) : <div className="text-slate-500">No activity yet</div>}
  </div>
);
