"use client";

import { UserButton } from "@clerk/nextjs";

import type { ChatSummary } from "@/lib/types";

type Props = {
  chats: ChatSummary[];
  activeChatId: string | null;
  onSelect: (chatId: string) => void;
  onDelete: (chatId: string) => void;
  onNewChat: () => void;
};

export function ChatSidebar({ chats, activeChatId, onSelect, onDelete, onNewChat }: Props) {
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-neutral-200">
      <div className="flex items-center justify-between px-4 py-4">
        <span className="text-sm font-medium">CampusPath</span>
        <UserButton />
      </div>

      <button
        type="button"
        className="mx-4 mb-3 border border-neutral-900 py-1.5 text-sm"
        onClick={onNewChat}
      >
        New chat
      </button>

      <nav className="min-h-0 flex-1 overflow-auto px-2">
        {chats.map((chat) => (
          <div
            key={chat.id}
            className={`flex items-center justify-between px-2 text-sm ${
              activeChatId === chat.id ? "bg-neutral-100" : "hover:bg-neutral-50"
            }`}
          >
            <button
              type="button"
              onClick={() => onSelect(chat.id)}
              className="min-w-0 flex-1 truncate py-2 text-left"
            >
              {chat.title}
            </button>
            <button
              type="button"
              aria-label={`Delete ${chat.title}`}
              className="ml-2 text-neutral-400"
              onClick={() => onDelete(chat.id)}
            >
              ×
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
