const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export async function getIntegrations() {
  const response = await fetch(`${API_URL}/integrations`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load integrations");
  return response.json();
}

export async function getActivities() {
  const response = await fetch(`${API_URL}/activities`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load activities");
  return response.json();
}

export async function connectIntegration(provider: string, webhookUrl?: string) {
  const response = await fetch(`${API_URL}/integrations/${provider}/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ webhook_url: webhookUrl || undefined }),
  });
  if (!response.ok) throw new Error("Failed to connect integration");
  return response.json();
}

export async function disconnectIntegration(provider: string) {
  const response = await fetch(`${API_URL}/integrations/${provider}/disconnect`, {
    method: "POST",
  });
  if (!response.ok) throw new Error("Failed to disconnect integration");
  return response.json();
}

export async function syncIntegration(provider: string, webhookUrl?: string) {
  const response = await fetch(`${API_URL}/integrations/${provider}/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ webhook_url: webhookUrl || undefined }),
  });
  if (!response.ok) throw new Error("Failed to sync integration");
  return response.json();
}

export async function getGmailAuthUrl(clientId?: string) {
  const url = clientId 
    ? `${API_URL}/integrations/gmail/auth-url?client_id=${encodeURIComponent(clientId)}`
    : `${API_URL}/integrations/gmail/auth-url`;
  const response = await fetch(url);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate Google OAuth URL");
  }
  return response.json();
}

export async function getGoogleDriveAuthUrl(clientId?: string) {
  const url = clientId 
    ? `${API_URL}/integrations/google_drive/auth-url?client_id=${encodeURIComponent(clientId)}`
    : `${API_URL}/integrations/google_drive/auth-url`;
  const response = await fetch(url);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate Google Drive OAuth URL");
  }
  return response.json();
}

export async function getSlackAuthUrl(clientId?: string) {
  const url = clientId 
    ? `${API_URL}/integrations/slack/auth-url?client_id=${encodeURIComponent(clientId)}`
    : `${API_URL}/integrations/slack/auth-url`;
  const response = await fetch(url);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate Slack OAuth URL");
  }
  return response.json();
}

export async function saveKeys(data: { google_client_id?: string; google_client_secret?: string; gemini_api_key?: string }) {
  const response = await fetch(`${API_URL}/integrations/gmail/save-keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to save credentials");
  return response.json();
}
