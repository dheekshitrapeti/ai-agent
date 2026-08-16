"use client";

import { useState } from "react";
import { connectIntegration, disconnectIntegration, getGmailAuthUrl, getGoogleDriveAuthUrl, getSlackAuthUrl, saveKeys, syncIntegration } from "@/lib/api";
import { CheckCircle2, Key, ExternalLink, RefreshCw, Unplug, Zap } from "lucide-react";

type Props = {
  provider: string;
  name: string;
  description: string;
  icon: string;
  initialStatus?: "connected" | "disconnected" | "error";
  initialWebhookUrl?: string | null;
  hasOauthConfig?: boolean;
  connectedAt?: string | null;
};

export function IntegrationCard({
  provider,
  name,
  description,
  icon,
  initialStatus = "disconnected",
  initialWebhookUrl,
  hasOauthConfig = false,
  connectedAt,
}: Props) {
  const [status, setStatus] = useState<string>(initialStatus);
  const [webhookUrl, setWebhookUrl] = useState<string>(
    initialWebhookUrl ?? (provider === "gmail" ? "http://localhost:5678/webhook/gmail-sync" : provider === "slack" ? "http://localhost:5678/webhook/slack-sync" : "http://localhost:5678/webhook/drive-sync")
  );
  const [showConfig, setShowConfig] = useState(false);
  const [showOAuthModal, setShowOAuthModal] = useState(false);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [geminiKey, setGeminiKey] = useState("");

  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleConnect = async () => {
    setLoading(true);
    setMessage(null);

    if (provider === "gmail") {
      try {
        const authData = await getGmailAuthUrl(clientId || undefined);
        if (authData.auth_url) {
          setMessage("Redirecting to Google OAuth2 consent screen...");
          window.location.href = authData.auth_url;
          return;
        }
      } catch (err: any) {
        setShowOAuthModal(true);
        setMessage("Please configure your Google Client ID & Secret below to connect.");
        setLoading(false);
        return;
      }
    } else if (provider === "google_drive") {
      try {
        const authData = await getGoogleDriveAuthUrl(clientId || undefined);
        if (authData.auth_url) {
          setMessage("Redirecting to Google Drive OAuth2 consent screen...");
          window.location.href = authData.auth_url;
          return;
        }
      } catch (err: any) {
        setShowOAuthModal(true);
        setMessage("Please configure your Google Client ID & Secret below to connect.");
        setLoading(false);
        return;
      }
    } else if (provider === "slack") {
      try {
        const authData = await getSlackAuthUrl(clientId || undefined);
        if (authData.auth_url) {
          setMessage("Redirecting to Slack OAuth2 consent screen...");
          window.location.href = authData.auth_url;
          return;
        }
      } catch (err: any) {
        setShowOAuthModal(true);
        setMessage("Please configure your Slack Client ID & Secret in backend/.env.");
        setLoading(false);
        return;
      }
    }

    try {
      const res = await connectIntegration(provider, webhookUrl);
      setStatus("connected");
      setMessage(res.message);
    } catch (err: any) {
      setMessage(`Connection failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveKeys = async () => {
    setLoading(true);
    try {
      await saveKeys({
        google_client_id: clientId,
        google_client_secret: clientSecret,
        gemini_api_key: geminiKey,
      });
      setMessage("Credentials saved! Initiating Google OAuth2 connection...");
      const authData = await getGmailAuthUrl(clientId);
      window.location.href = authData.auth_url;
    } catch (err: any) {
      setMessage(`Save failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await disconnectIntegration(provider);
      setStatus("disconnected");
      setMessage(res.message);
    } catch (err: any) {
      setMessage(`Disconnect failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setMessage(null);
    try {
      const res = await syncIntegration(provider, webhookUrl);
      setMessage(res.message);
    } catch (err: any) {
      setMessage(`Sync failed: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const isConnected = status === "connected";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-2xl">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-slate-900">{name}</h2>
            {isConnected ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 border border-emerald-200">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Connected
              </span>
            ) : (
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
                Disconnected
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {isConnected ? (
            <>
              <button
                type="button"
                onClick={handleSync}
                disabled={syncing}
                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-50 px-3.5 py-2 text-sm font-medium text-indigo-600 hover:bg-indigo-100 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
                {syncing ? "Syncing..." : "Sync Now"}
              </button>
              <button
                type="button"
                onClick={handleDisconnect}
                disabled={loading}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-red-600 disabled:opacity-50"
              >
                <Unplug className="h-4 w-4" />
                Disconnect
              </button>
            </>
          ) : (
            <button
              type="button"
              data-provider={provider}
              onClick={handleConnect}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 shadow-sm"
            >
              {loading ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : provider === "gmail" ? (
                <ExternalLink className="h-4 w-4 text-blue-400" />
              ) : (
                <Zap className="h-4 w-4 text-yellow-400 fill-yellow-400" />
              )}
              {loading ? "Connecting..." : provider === "gmail" ? "Connect with Google OAuth2" : "Connect"}
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowConfig(!showConfig)}
            className="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            title="n8n Webhook & Credentials Settings"
          >
            ⚙️
          </button>
        </div>
      </div>

      {(showOAuthModal || (showConfig && provider === "gmail")) && (
        <div className="mt-4 rounded-xl border border-blue-200 bg-blue-50/50 p-4 text-sm space-y-3">
          <div className="flex items-center gap-2 font-semibold text-slate-900">
            <Key className="h-4 w-4 text-blue-600" />
            <span>Google OAuth2 & Gemini Credentials</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-slate-700">Google Client ID</label>
              <input
                type="text"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="xxxxxx.apps.googleusercontent.com"
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700">Google Client Secret</label>
              <input
                type="password"
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
                placeholder="GOCSPX-xxxxxx"
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700">Google Gemini API Key</label>
            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="AIzaSyxxxxxx"
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
            />
          </div>

          <p className="text-xs text-slate-500">
            <strong>Redirect URI:</strong> <code>http://localhost:8000/api/integrations/gmail/callback</code>
          </p>

          <button
            type="button"
            onClick={handleSaveKeys}
            disabled={loading}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Save Credentials & Connect to Google
          </button>
        </div>
      )}

      {showConfig && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
          <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">
            n8n Trigger Webhook URL
          </label>
          <div className="mt-1.5 flex gap-2">
            <input
              type="text"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="http://localhost:5678/webhook/gmail-sync"
              className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-slate-800 text-xs focus:border-slate-900 focus:outline-none"
            />
          </div>
          <p className="mt-1 text-xs text-slate-500">
            When you click Connect or Sync, this URL is called to execute your n8n workflow.
          </p>
        </div>
      )}

      {message && (
        <div
          className={`mt-4 flex items-start gap-2.5 rounded-xl px-4 py-3 text-sm ${
            message.includes("failed") || message.includes("Error") || message.includes("Please configure")
              ? "bg-amber-50 text-amber-800 border border-amber-200"
              : "bg-emerald-50 text-emerald-800 border border-emerald-200"
          }`}
        >
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
          <span>{message}</span>
        </div>
      )}
    </div>
  );
}
