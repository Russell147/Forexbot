export const f = (n: number, d = 2) => Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
export const sg = (n: number) => (n >= 0 ? "+" : "−") + "$" + f(Math.abs(n));
export const tone = (n: number) => (n >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400");
