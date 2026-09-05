"use client";

import { TableToolbar } from "@/components/comparison/TableToolbar";
import { chatsApi, collegesApi, columnsApi } from "@/lib/api";
import type { ChatDetail } from "@/lib/types";

type Props = {
  token: string;
  chat: ChatDetail;
  onChange: (chat: ChatDetail) => void;
};

/** Colleges as rows, default and custom columns across. Cells stay empty until the agent pass. */
export function ComparisonTable({ token, chat, onChange }: Props) {
  async function refresh() {
    onChange(await chatsApi.get(token, chat.id));
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <TableToolbar
        token={token}
        major={chat.major}
        onMajorChange={async (major) => {
          onChange(await chatsApi.update(token, chat.id, { major }));
        }}
        onAddCollege={async (college) => {
          await collegesApi.add(token, chat.id, {
            name: college.name,
            country: college.country,
          });
          await refresh();
        }}
        onAddColumn={async (label) => {
          await columnsApi.add(token, chat.id, label);
          await refresh();
        }}
      />

      <div className="min-h-0 flex-1 overflow-auto">
        {chat.colleges.length === 0 ? (
          <p className="px-6 py-10 text-sm text-neutral-500">Add a college to start the table.</p>
        ) : (
          <table className="min-w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-neutral-200">
                <th className="sticky left-0 bg-[#fafafa] px-6 py-3 font-medium">College</th>
                {chat.columns.map((column) => (
                  <th key={column.id} className="whitespace-nowrap px-4 py-3 font-medium">
                    <span>{column.label}</span>
                    {!column.is_default && (
                      <button
                        type="button"
                        aria-label={`Remove ${column.label}`}
                        className="ml-2 text-neutral-400"
                        onClick={async () => {
                          await columnsApi.remove(token, chat.id, column.id);
                          await refresh();
                        }}
                      >
                        ×
                      </button>
                    )}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {chat.colleges.map((college) => (
                <tr key={college.id} className="border-b border-neutral-200 align-top">
                  <td className="sticky left-0 bg-[#fafafa] px-6 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div>{college.name}</div>
                        {college.country && (
                          <div className="text-xs text-neutral-400">{college.country}</div>
                        )}
                        <input
                          defaultValue={college.major_override ?? ""}
                          placeholder={chat.major ? `Major: ${chat.major}` : "Major override"}
                          onBlur={async (event) => {
                            await collegesApi.setMajorOverride(
                              token,
                              chat.id,
                              college.id,
                              event.target.value.trim() || null,
                            );
                            await refresh();
                          }}
                          className="mt-1 w-40 border-b border-transparent bg-transparent text-xs text-neutral-500 outline-none hover:border-neutral-300 focus:border-neutral-400"
                        />
                      </div>
                      <button
                        type="button"
                        aria-label={`Remove ${college.name}`}
                        className="text-neutral-400"
                        onClick={async () => {
                          await collegesApi.remove(token, chat.id, college.id);
                          await refresh();
                        }}
                      >
                        ×
                      </button>
                    </div>
                  </td>

                  {chat.columns.map((column) => {
                    const cell = college.cells.find((item) => item.column_id === column.id);
                    return (
                      <td key={column.id} className="px-4 py-3 text-neutral-400">
                        {cell?.value || "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
