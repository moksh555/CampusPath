import { request } from "@/lib/api/client";
import type { Column } from "@/lib/types";

export const columnsApi = {
  add: (token: string, chatId: string, label: string) =>
    request<Column>(`/chats/${chatId}/columns`, token, {
      method: "POST",
      body: JSON.stringify({ label }),
    }),

  remove: (token: string, chatId: string, columnId: string) =>
    request<void>(`/chats/${chatId}/columns/${columnId}`, token, { method: "DELETE" }),
};
