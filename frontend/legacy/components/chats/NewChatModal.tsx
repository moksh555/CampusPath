"use client";

import { useState } from "react";

import { CollegeChips } from "@/components/colleges/CollegeChips";
import { CollegeSearchInput } from "@/components/colleges/CollegeSearchInput";
import type { NewChatPayload } from "@/lib/api";
import type { CollegeSearchResult } from "@/lib/types";

type Props = {
  token: string;
  onClose: () => void;
  onCreate: (payload: NewChatPayload) => Promise<void>;
};

export function NewChatModal({ token, onClose, onCreate }: Props) {
  const [major, setMajor] = useState("");
  const [colleges, setColleges] = useState<CollegeSearchResult[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // The backend enforces the same rule; this keeps the button honest.
  const canSubmit = colleges.length >= 1 || major.trim().length > 0;

  async function submit() {
    if (!canSubmit || busy) return;
    setBusy(true);
    setError("");
    try {
      await onCreate({
        major: major.trim() || undefined,
        colleges: colleges.map((college) => ({
          name: college.name,
          country: college.country,
        })),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create chat");
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/20 p-4">
      <div className="w-full max-w-md border border-neutral-200 bg-white p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium">New chat</h2>
          <button type="button" className="text-sm text-neutral-500" onClick={onClose}>
            Close
          </button>
        </div>

        <label className="mb-4 block text-sm">
          <span className="text-neutral-500">Major</span>
          <input
            value={major}
            onChange={(event) => setMajor(event.target.value)}
            placeholder="e.g. Computer Science"
            className="mt-1 w-full border-b border-neutral-300 bg-transparent py-1.5 outline-none"
          />
        </label>

        <div className="mb-3 text-sm">
          <span className="text-neutral-500">Colleges</span>
          <CollegeSearchInput
            token={token}
            onPick={(college) =>
              setColleges((current) =>
                current.some((item) => item.name === college.name && item.country === college.country)
                  ? current
                  : [...current, college],
              )
            }
          />
          <CollegeChips
            colleges={colleges}
            onRemove={(college) =>
              setColleges((current) =>
                current.filter(
                  (item) => !(item.name === college.name && item.country === college.country),
                ),
              )
            }
          />
        </div>

        <p className="mb-4 text-xs text-neutral-400">College or major is required.</p>
        {error && <p className="mb-3 text-xs text-red-600">{error}</p>}

        <button
          type="button"
          disabled={!canSubmit || busy}
          onClick={submit}
          className="w-full border border-neutral-900 py-2 text-sm disabled:border-neutral-300 disabled:text-neutral-400"
        >
          {busy ? "Creating…" : "Start"}
        </button>
      </div>
    </div>
  );
}
