export type Dir = "BUY" | "SELL";
export interface Position { id: number; sym: string; dir: Dir; entry: number; sl: number; tp: number; lot: number; strat: string; pnl: number; slp: number; rr: number }
export interface Trade extends Position { exit: number; why: string; time: string; day: boolean }
export interface Risk { perTrade: number; maxDaily: number; maxDD: number; maxPos: number; minRR: number; maxSpread: number; closeOnStop: boolean; session: string; maxDailyTrades: number; maxConsecutiveLosses: number; trailingEnabled?: boolean; trailingAtrMult?: number }
export interface LogEntry { t: string; m: string }
export interface Strategy { on: boolean; tf: string }
