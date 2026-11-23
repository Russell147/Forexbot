export function Line({ data, height = 160, className = "stroke-brand", strokeWidth = 2 }: { data: number[]; height?: number; className?: string; strokeWidth?: number }) {
  if (data.length < 2) return <div className="text-sm text-slate-500">Not enough data</div>;
  const w = 600, mn = Math.min(...data), r = Math.max(...data) - mn || 1;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${height - 6 - ((v - mn) / r) * (height - 12)}`).join(" ");
  return <svg viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none" className="w-full" style={{ height }}><polyline fill="none" className={className} strokeWidth={strokeWidth} vectorEffect="non-scaling-stroke" points={pts} /></svg>;
}
