import { config } from "./configuration";
let refreshing: Promise<Response> | null = null;
export async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const response = await fetch(config.apiUrl + path, {
    signal: AbortSignal.timeout(20000),
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (response.status === 401 && retry && path !== "/auth/refresh") {
    if (!refreshing)
      refreshing = fetch(config.apiUrl + "/auth/refresh", {
        method: "POST",
        signal: AbortSignal.timeout(20000),
        credentials: "include",
      }).finally(() => {
        refreshing = null;
      });
    const renewed = await refreshing;
    if (renewed.ok) return request<T>(path, options, false);
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      typeof payload.detail === "string"
        ? payload.detail
        : `Request failed (${response.status})`,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const post = <T>(path: string, data: unknown = {}) =>
  request<T>(path, { method: "POST", body: JSON.stringify(data) });
export const patch = <T>(path: string, data: unknown) =>
  request<T>(path, { method: "PATCH", body: JSON.stringify(data) });
export const remove = (path: string) =>
  request<void>(path, { method: "DELETE" });
