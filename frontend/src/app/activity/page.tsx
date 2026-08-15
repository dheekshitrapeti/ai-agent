import { Activity as ActivityIcon, FileText, Mail, MessageSquare } from "lucide-react";
import { getActivities } from "@/lib/api";

type Activity = {
  id: number;
  source: "slack" | "gmail" | "google_drive";
  title: string | null;
  sender: string | null;
  summary: string | null;
  source_url: string | null;
  event_created_at: string | null;
};

const sourceIcons = {
  slack: MessageSquare,
  gmail: Mail,
  google_drive: FileText,
};

export default async function ActivityPage() {
  let activities: Activity[] = [];
  let loadError = false;

  try {
    activities = await getActivities();
  } catch {
    loadError = true;
  }

  return (
    <div className="p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <p className="text-sm font-medium text-slate-500">Activity</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Unified activity</h1>
        {loadError ? (
          <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
            Could not load activity. Confirm that the API and database are running.
          </div>
        ) : activities.length === 0 ? (
          <div className="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
            <ActivityIcon className="mx-auto h-8 w-8 text-slate-400" />
            <h2 className="mt-4 text-lg font-semibold">No activity yet</h2>
            <p className="mt-2 text-sm text-slate-500">n8n events will appear here after integrations are connected.</p>
          </div>
        ) : (
          <div className="mt-8 space-y-3">
            {activities.map((activity) => {
              const Icon = sourceIcons[activity.source];
              return (
                <article key={activity.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex gap-4">
                    <Icon className="mt-0.5 h-5 w-5 shrink-0 text-slate-500" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <h2 className="font-semibold text-slate-900">{activity.title ?? "Untitled activity"}</h2>
                        {activity.event_created_at && (
                          <time className="text-xs text-slate-500" dateTime={activity.event_created_at}>
                            {new Date(activity.event_created_at).toLocaleString()}
                          </time>
                        )}
                      </div>
                      {activity.sender && <p className="mt-1 text-sm text-slate-500">{activity.sender}</p>}
                      {activity.summary && <p className="mt-3 text-sm text-slate-700">{activity.summary}</p>}
                      {activity.source_url && (
                        <a className="mt-3 inline-block text-sm font-medium text-blue-600 hover:text-blue-800" href={activity.source_url} target="_blank" rel="noreferrer">
                          Open in {activity.source === "gmail" ? "Gmail" : activity.source === "slack" ? "Slack" : "Google Drive"}
                        </a>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
