import { request } from "@/lib/api";
import type { University } from "@/features/sessions/types";

const CACHE_KEY = "campuspath-university-directory-v1";
const MAX_AGE = 60 * 60 * 1000;
type Cache = { expires: number; rows: University[] };
let memory: Cache | undefined;
let pending: Promise<University[]> | undefined;

function validCache(value: unknown): value is Cache {
  if (!value || typeof value !== "object") return false;
  const cache = value as Cache;
  return (
    typeof cache.expires === "number" &&
    cache.expires > Date.now() &&
    Array.isArray(cache.rows) &&
    cache.rows.every(
      (row) =>
        row &&
        typeof row.name === "string" &&
        (row.country === null || typeof row.country === "string"),
    )
  );
}

export async function loadDirectory(): Promise<University[]> {
  if (memory && memory.expires > Date.now()) return memory.rows;
  try {
    const stored: unknown = JSON.parse(
      sessionStorage.getItem(CACHE_KEY) || "null",
    );
    if (validCache(stored)) {
      memory = stored;
      return stored.rows;
    }
  } catch {
    /* Storage may be unavailable; keep an in-memory cache. */
  }
  if (!pending) {
    pending = request<University[]>("/colleges/directory")
      .then((rows) => {
        const cache = { expires: Date.now() + MAX_AGE, rows };
        if (!validCache(cache)) throw new Error("Invalid university directory");
        memory = cache;
        try {
          sessionStorage.setItem(CACHE_KEY, JSON.stringify(cache));
        } catch {
          /* Storage is optional. */
        }
        return rows;
      })
      .finally(() => {
        pending = undefined;
      });
  }
  return pending;
}

export function searchDirectory(
  rows: University[],
  query: string,
): University[] {
  const normalized = query.trim().toLowerCase();
  if (normalized.length < 2) return [];
  const terms = normalized.split(/\s+/);
  return rows
    .filter((row) => {
      const text = `${row.name} ${row.country ?? ""}`.toLowerCase();
      return terms.every((term) => text.includes(term));
    })
    .sort(
      (a, b) =>
        Number(!a.name.toLowerCase().startsWith(normalized)) -
          Number(!b.name.toLowerCase().startsWith(normalized)) ||
        a.name.localeCompare(b.name),
    )
    .slice(0, 12);
}
