import { Activity, FileText, Mail, MessageSquare } from "lucide-react";
import { getActivities } from "@/lib/api";
import Link from "next/link";

type ActivityItem = {
  id: number;
  source: "slack" | "gmail" | "google_drive";
  title: string | null;
  sender: string | null;
  summary: string | null;
  source_url: string | null;
  event_created_at: string | null;
};

export default async function DashboardPage() {
  let activities: ActivityItem[] = [];

  try {
    activities = await getActivities();
  } catch (e) {
    // API server offline fallback
  }

  const slackCount = activities.filter((a) => a.source === "slack").length;
  const emailCount = activities.filter((a) => a.source === "gmail").length;
  const driveCount = activities.filter((a) => a.source === "google_drive").length;

  const stats = [
    { label: "Slack messages", Icon: MessageSquare, count: slackCount },
    { label: "Emails", Icon: Mail, count: emailCount },
    { label: "Drive documents", Icon: FileText, count: driveCount },
  ];

  return (
    <div className="p-6 md:p-10">
      <div className="mx-auto max-w-6xl">
        <p className="text-sm font-medium text-slate-500">Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">AI Workspace</h1>
        <p className="mt-2 text-slate-600">Connect your workplace tools and get a unified activity feed.</p>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {stats.map(({ label, Icon, count }) => (
            <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <Icon className="mb-5 h-5 w-5 text-slate-500" />
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-1 text-3xl font-semibold text-slate-900">{count}</p>
            </div>
          ))}
        </div>

        {activities.length === 0 ? (
          <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <Activity className="mx-auto h-8 w-8 text-slate-400" />
            <h2 className="mt-4 text-lg font-semibold text-slate-900">No activity yet</h2>
            <p className="mt-2 text-sm text-slate-500">
              Connect Gmail, Slack or Google Drive in the{" "}
              <Link href="/integrations" className="font-medium text-blue-600 hover:underline">
                Integrations tab
              </Link>{" "}
              to start receiving live activity summaries.
            </p>
          </div>
        ) : (
          <div className="mt-8">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Recent Activities</h2>
              <Link href="/activity" className="text-sm font-medium text-blue-600 hover:underline">
                View all ({activities.length}) &rarr;
              </Link>
            </div>

            <div className="mt-4 space-y-3">
              {activities.slice(0, 5).map((activity) => (
                <div key={activity.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-start gap-4">
                    <Mail className="mt-0.5 h-5 w-5 shrink-0 text-indigo-500" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <h3 className="font-semibold text-slate-900">{activity.title ?? "Untitled Email"}</h3>
                        {activity.event_created_at && (
                          <time className="text-xs text-slate-500">
                            {new Date(activity.event_created_at).toLocaleString()}
                          </time>
                        )}
                      </div>
                      {activity.sender && <p className="mt-0.5 text-sm text-slate-500">{activity.sender}</p>}
                      {activity.summary && <p className="mt-2 text-sm text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-100">{activity.summary}</p>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
