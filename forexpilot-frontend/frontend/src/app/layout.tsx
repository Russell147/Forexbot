import type { Metadata } from "next";
import "@/styles/globals.css";
export const metadata: Metadata = { title: "ForexPilot AI", description: "Automated Forex trading dashboard" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
