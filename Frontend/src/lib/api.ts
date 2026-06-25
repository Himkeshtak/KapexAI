const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export async function getApiHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, {
      cache: "no-store",
      signal,
    });
    return response.ok;
  } catch {
    return false;
  }
}
