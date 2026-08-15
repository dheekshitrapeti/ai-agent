"use client";

import { useState } from "react";

type Props = { provider: string; name: string; description: string; icon: string };

export function IntegrationCard({ provider, name, description, icon }: Props) {
  const [message, setMessage] = useState("");

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-2xl">{icon}</div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold">{name}</h2>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">Disconnected</span>
          </div>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>
        <button
          type="button"
          data-provider={provider}
          onClick={() => setMessage(`${name} OAuth will be implemented in Phase 3.`)}
          className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
        >
          Connect
        </button>
      </div>
      {message && <div className="mt-4 rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600">{message}</div>}
    </div>
  );
}
