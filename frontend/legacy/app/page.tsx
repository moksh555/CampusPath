"use client";

import { useEffect, useState } from "react";

import { ChatSidebar } from "@/components/chats/ChatSidebar";
import { NewChatModal } from "@/components/chats/NewChatModal";
import { ComparisonTable } from "@/components/comparison/ComparisonTable";
import { chatsApi } from "@/lib/api";
import { useAuthToken } from "@/lib/hooks/useAuthToken";
import type { ChatDetail, ChatSummary } from "@/lib/types";

export default function HomePage() {
  const { token, isReady } = useAuthToken();
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [activeChat, setActiveChat] = useState<ChatDetail | null>(null);
  const [showNewChat, setShowNewChat] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    chatsApi
      .list(token)
      .then(setChats)
      .catch((err: Error) => setError(err.message));
  }, [token]);

  if (!isReady || !token) {
    return <main className="p-8 text-sm text-neutral-500">Loading…</main>;
  }

  return (
    <div className="flex h-screen">
      <ChatSidebar
        chats={chats}
        activeChatId={activeChat?.id ?? null}
        onNewChat={() => setShowNewChat(true)}
        onSelect={async (chatId) => {
          setError("");
          try {
            setActiveChat(await chatsApi.get(token, chatId));
          } catch (err) {
            setError(err instanceof Error ? err.message : "Could not open chat");
          }
        }}
        onDelete={async (chatId) => {
          await chatsApi.remove(token, chatId);
          setChats((current) => current.filter((item) => item.id !== chatId));
          setActiveChat((current) => (current?.id === chatId ? null : current));
        }}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        {error && <p className="px-6 py-3 text-sm text-red-600">{error}</p>}

        {activeChat ? (
          <ComparisonTable
            token={token}
            chat={activeChat}
            onChange={(chat) => {
              setActiveChat(chat);
              setChats((current) =>
                current.map((item) =>
                  item.id === chat.id ? { ...item, title: chat.title, major: chat.major } : item,
                ),
              );
            }}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center text-sm text-neutral-500">
            Start a chat to compare colleges.
          </div>
        )}
      </main>

      {showNewChat && (
        <NewChatModal
          token={token}
          onClose={() => setShowNewChat(false)}
          onCreate={async (payload) => {
            const created = await chatsApi.create(token, payload);
            setChats((current) => [created, ...current]);
            setActiveChat(created);
            setShowNewChat(false);
          }}
        />
      )}
    </div>
  );
}
