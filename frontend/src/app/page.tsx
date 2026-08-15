import { Activity, FileText, Mail, MessageSquare } from "lucide-react";

const stats = [
  ["Slack messages", MessageSquare],
  ["Emails", Mail],
  ["Drive documents", FileText],
] as const;

export default function DashboardPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mx-auto max-w-6xl">
        <p className="text-sm font-medium text-slate-500">Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">AI Workspace</h1>
        <p className="mt-2 text-slate-600">Connect your workplace tools and get a unified activity feed.</p>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {stats.map(([label, Icon]) => (
            <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <Icon className="mb-5 h-5 w-5 text-slate-500" />
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-1 text-3xl font-semibold">0</p>
            </div>
          ))}
        </div>

        <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <Activity className="mx-auto h-8 w-8 text-slate-400" />
          <h2 className="mt-4 text-lg font-semibold">No activity yet</h2>
          <p className="mt-2 text-sm text-slate-500">Connect Slack, Gmail or Google Drive to start receiving activity.</p>
        </div>
      </div>
    </div>
  );
}
