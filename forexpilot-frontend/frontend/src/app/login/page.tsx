"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Btn, Card } from "@/components/ui";
import { SIMULATOR_MODE } from "@/lib/store";
import { api } from "@/services/api";

export default function Login() {
  const r = useRouter();
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [registering, setRegistering] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const input = "w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-950";
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    if (SIMULATOR_MODE) {
      r.replace("/dashboard");
      return;
    }
    setBusy(true);
    try {
      if (registering) await api.register(email, pw);
      await api.login(email, pw);
      r.replace("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="mx-auto mt-24 max-w-sm px-4">
      <Card title={SIMULATOR_MODE ? "ForexPilot AI simulator" : registering ? "Create your account" : "Sign in to ForexPilot AI"}>
        <form className="space-y-3" onSubmit={submit}>
          <input className={input} type="email" placeholder="Email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className={input} type="password" placeholder="Password" autoComplete={registering ? "new-password" : "current-password"} minLength={registering ? 8 : undefined} required value={pw} onChange={(e) => setPw(e.target.value)} />
          {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
          <Btn type="submit" disabled={busy} variant="primary" className="w-full">{busy ? "Please wait…" : registering ? "Create account" : "Sign in"}</Btn>
          {!SIMULATOR_MODE && <button type="button" className="w-full text-sm text-brand underline" onClick={() => { setError(null); setRegistering(!registering); }}>
            {registering ? "Already have an account? Sign in" : "Create the first account"}
          </button>}
          {SIMULATOR_MODE && <p className="text-xs text-slate-500">Simulator mode is enabled. Set NEXT_PUBLIC_USE_SIMULATOR=false to connect to the backend.</p>}
        </form>
      </Card>
    </div>
  );
}
