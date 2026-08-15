import { IntegrationCard } from "@/components/integrations/IntegrationCard";

const integrations = [
  { provider: "slack", name: "Slack", description: "Receive and summarize new Slack messages.", icon: "💬" },
  { provider: "gmail", name: "Gmail", description: "Summarize incoming emails.", icon: "✉️" },
  { provider: "google_drive", name: "Google Drive", description: "Track newly uploaded documents.", icon: "📁" },
];

export default function IntegrationsPage() {
  return (
    <div className="p-6 md:p-10">
      <div className="mx-auto max-w-4xl">
        <p className="text-sm font-medium text-slate-500">Integrations</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Connect your tools</h1>
        <p className="mt-2 text-slate-600">OAuth connection will be implemented in Phase 3.</p>
        <div className="mt-8 space-y-4">
          {integrations.map((item) => <IntegrationCard key={item.provider} {...item} />)}
        </div>
      </div>
    </div>
  );
}
