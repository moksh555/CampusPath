"use client";

import { useEffect, useState } from "react";

import { collegeDirectoryApi } from "@/lib/api";
import type { CollegeSearchResult } from "@/lib/types";

type Props = {
  token: string;
  onPick: (college: CollegeSearchResult) => void;
  placeholder?: string;
};

/**
 * Autocomplete over the worldwide university directory. Any typed name can be
 * used as-is, so schools missing from the directory still work.
 */
export function CollegeSearchInput({ token, onPick, placeholder = "Add a college" }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CollegeSearchResult[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults([]);
      return;
    }
    const handle = window.setTimeout(async () => {
      try {
        setResults(await collegeDirectoryApi.search(token, trimmed));
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 250);
    return () => window.clearTimeout(handle);
  }, [query, token]);

  function pick(college: CollegeSearchResult) {
    onPick(college);
    setQuery("");
    setResults([]);
    setOpen(false);
  }

  function useTypedName() {
    const name = query.trim();
    if (name) pick({ name, country: null });
  }

  return (
    <div className="relative">
      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            useTypedName();
          }
        }}
        placeholder={placeholder}
        className="w-full border-b border-neutral-300 bg-transparent py-1.5 outline-none placeholder:text-neutral-400"
      />

      {open && (results.length > 0 || query.trim()) && (
        <ul className="absolute z-10 mt-1 max-h-56 w-full overflow-auto border border-neutral-200 bg-white text-sm">
          {results.map((item) => (
            <li key={`${item.name}-${item.country}`}>
              <button
                type="button"
                className="flex w-full items-baseline gap-2 px-2 py-1.5 text-left hover:bg-neutral-50"
                onClick={() => pick(item)}
              >
                <span>{item.name}</span>
                {item.country && <span className="text-neutral-400">{item.country}</span>}
              </button>
            </li>
          ))}
          {query.trim() && (
            <li>
              <button
                type="button"
                className="w-full px-2 py-1.5 text-left text-neutral-600 hover:bg-neutral-50"
                onClick={useTypedName}
              >
                Use “{query.trim()}”
              </button>
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
