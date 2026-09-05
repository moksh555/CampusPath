const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Calls the FastAPI backend with a Clerk bearer token attached. */
export async function request<T>(
  path: string,
  token: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      if (typeof payload.detail === "string") detail = payload.detail;
    } catch {
      // Keep the status text when the body is not JSON.
    }
    throw new Error(detail);
  }

  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}
