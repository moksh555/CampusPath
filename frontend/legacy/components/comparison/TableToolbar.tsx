"use client";

import { useState } from "react";

import { CollegeSearchInput } from "@/components/colleges/CollegeSearchInput";
import type { CollegeSearchResult } from "@/lib/types";

type Props = {
  token: string;
  major: string | null;
  onMajorChange: (major: string | null) => void;
  onAddCollege: (college: CollegeSearchResult) => Promise<void>;
  onAddColumn: (label: string) => Promise<void>;
};

/** Chat-wide major plus the add-college and add-column entry points. */
export function TableToolbar({ token, major, onMajorChange, onAddCollege, onAddColumn }: Props) {
  const [majorDraft, setMajorDraft] = useState(major ?? "");
  const [columnLabel, setColumnLabel] = useState("");
  const [addingCollege, setAddingCollege] = useState(false);
  const [addingColumn, setAddingColumn] = useState(false);

  return (
    <>
      <header className="flex flex-wrap items-end gap-6 border-b border-neutral-200 px-6 py-4">
        <label className="text-sm">
          <span className="mr-2 text-neutral-500">Major</span>
          <input
            value={majorDraft}
            onChange={(event) => setMajorDraft(event.target.value)}
            onBlur={() => {
              const next = majorDraft.trim();
              if (next !== (major ?? "")) onMajorChange(next || null);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") (event.target as HTMLInputElement).blur();
            }}
            placeholder="All colleges"
            className="w-48 border-b border-neutral-300 bg-transparent py-0.5 outline-none"
          />
        </label>

        <button
          type="button"
          className="text-sm text-neutral-600"
          onClick={() => setAddingCollege((open) => !open)}
        >
          Add college
        </button>
        <button
          type="button"
          className="text-sm text-neutral-600"
          onClick={() => setAddingColumn((open) => !open)}
        >
          Add column
        </button>
      </header>

      {(addingCollege || addingColumn) && (
        <div className="grid gap-3 border-b border-neutral-200 px-6 py-3 sm:grid-cols-2">
          {addingCollege && (
            <CollegeSearchInput
              token={token}
              placeholder="Search or type a college, then Enter"
              onPick={async (college) => {
                await onAddCollege(college);
                setAddingCollege(false);
              }}
            />
          )}
          {addingColumn && (
            <input
              value={columnLabel}
              onChange={(event) => setColumnLabel(event.target.value)}
              onKeyDown={async (event) => {
                if (event.key !== "Enter" || !columnLabel.trim()) return;
                await onAddColumn(columnLabel.trim());
                setColumnLabel("");
                setAddingColumn(false);
              }}
              placeholder="Column name, then Enter"
              className="border-b border-neutral-300 bg-transparent py-1.5 outline-none"
            />
          )}
        </div>
      )}
    </>
  );
}
