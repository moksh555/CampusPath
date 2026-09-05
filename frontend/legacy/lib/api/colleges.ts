import { request } from "@/lib/api/client";
import type { College, CollegeSearchResult } from "@/lib/types";

/** College rows inside one chat. */
export const collegesApi = {
  add: (token: string, chatId: string, body: { name: string; country?: string | null }) =>
    request<College>(`/chats/${chatId}/colleges`, token, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  setMajorOverride: (token: string, chatId: string, rowId: string, majorOverride: string | null) =>
    request<College>(`/chats/${chatId}/colleges/${rowId}`, token, {
      method: "PATCH",
      body: JSON.stringify({ major_override: majorOverride }),
    }),

  remove: (token: string, chatId: string, rowId: string) =>
    request<void>(`/chats/${chatId}/colleges/${rowId}`, token, { method: "DELETE" }),
};

/** Worldwide university lookup used by the autocomplete. */
export const collegeDirectoryApi = {
  search: (token: string, query: string) =>
    request<CollegeSearchResult[]>(`/colleges/search?q=${encodeURIComponent(query)}`, token),
};
