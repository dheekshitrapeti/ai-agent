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
