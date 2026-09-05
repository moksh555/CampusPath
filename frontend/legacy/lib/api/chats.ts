import { request } from "@/lib/api/client";
import type { ChatDetail, ChatSummary } from "@/lib/types";

export type NewChatPayload = {
  major?: string;
  colleges: { name: string; country?: string | null }[];
};

export const chatsApi = {
  list: (token: string) => request<ChatSummary[]>("/chats", token),

  get: (token: string, chatId: string) => request<ChatDetail>(`/chats/${chatId}`, token),

  create: (token: string, body: NewChatPayload) =>
    request<ChatDetail>("/chats", token, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  update: (token: string, chatId: string, body: { title?: string; major?: string | null }) =>
    request<ChatDetail>(`/chats/${chatId}`, token, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  remove: (token: string, chatId: string) =>
    request<void>(`/chats/${chatId}`, token, { method: "DELETE" }),
};
