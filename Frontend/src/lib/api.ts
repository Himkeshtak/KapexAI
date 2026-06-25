import {
  AgentSummary,
  ConsultationRequest,
  ConsultationResponse,
} from "@/lib/chat";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getApiHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    await apiRequest<{ status: string }>("/health", { signal });
    return true;
  } catch {
    return false;
  }
}

export async function getAgents(signal?: AbortSignal): Promise<AgentSummary[]> {
  const response = await apiRequest<{ agents: AgentSummary[] }>("/agents", {
    signal,
  });
  return response.agents;
}

export async function submitConsultation(
  request: ConsultationRequest,
  signal?: AbortSignal,
): Promise<ConsultationResponse> {
  return apiRequest<ConsultationResponse>("/consult", {
    method: "POST",
    body: JSON.stringify(request),
    signal,
  });
}
