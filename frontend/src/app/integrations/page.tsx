import { IntegrationCard } from "@/components/integrations/IntegrationCard";
import { getIntegrations } from "@/lib/api";

type IntegrationItem = {
  provider: string;
  name: string;
  description: string;
  icon: string;
  status: "connected" | "disconnected" | "error";
  n8n_webhook_url?: string | null;
  has_oauth_config?: boolean;
  connected_at?: string | null;
};

const defaultIntegrations: IntegrationItem[] = [
  { provider: "slack", name: "Slack", description: "Receive and summarize new Slack messages.", icon: "💬", status: "disconnected" },
  { provider: "gmail", name: "Gmail", description: "Summarize incoming emails via Google OAuth2.", icon: "✉️", status: "disconnected" },
  { provider: "google_drive", name: "Google Drive", description: "Track newly uploaded documents.", icon: "📁", status: "disconnected" },
];

export default async function IntegrationsPage({
  searchParams,
}: {
  searchParams?: Promise<{ connected?: string; error?: string }>;
}) {
  const params = (await searchParams) || {};
  let integrations: IntegrationItem[] = defaultIntegrations;

  try {
    integrations = await getIntegrations();
  } catch (e) {
    // Fallback to defaults if backend is not started yet
  }

  return (
    <div className="p-6 md:p-10">
      <div className="mx-auto max-w-4xl">
        <p className="text-sm font-medium text-slate-500">Integrations</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Connect your tools</h1>
        <p className="mt-2 text-slate-600">
          Click <strong>Connect with Google OAuth2</strong> on Gmail to authenticate with Google, authorize Gmail access, and trigger your n8n workflow.
        </p>

        {params.connected === "gmail" && (
          <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 flex items-center gap-2">
            <span>🎉</span>
            <span>Google OAuth2 authentication successful! Gmail is now connected.</span>
          </div>
        )}

        {params.error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            Google OAuth authentication error: {params.error}
          </div>
        )}

        <div className="mt-8 space-y-4">
          {integrations.map((item) => (
            <IntegrationCard
              key={item.provider}
              provider={item.provider}
              name={item.name}
              description={item.description}
              icon={item.icon}
              initialStatus={item.status}
              initialWebhookUrl={item.n8n_webhook_url}
              hasOauthConfig={item.has_oauth_config}
              connectedAt={item.connected_at}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
