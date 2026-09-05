"use client";
import { useEffect, useState } from "react";
import { loadDirectory, searchDirectory } from "./directory";
import type { University } from "@/features/sessions/types";
export function UniversityPicker({
  onAdd,
}: {
  onAdd: (university: University) => void;
}) {
  const [query, setQuery] = useState("");
  const [directory, setDirectory] = useState<University[]>([]);
  const [active, setActive] = useState(false);
  const [error, setError] = useState("");
  const results = searchDirectory(directory, query);
  useEffect(() => {
    if (!active) return;
    let alive = true;
    loadDirectory()
      .then((rows) => {
        if (alive) setDirectory(rows);
      })
      .catch(() => {
        if (alive)
          setError(
            "Directory unavailable. You can still add this university by name.",
          );
      });
    return () => {
      alive = false;
    };
  }, [active]);
  function pick(item: University) {
    onAdd(item);
    setQuery("");
  }
  return (
    <div className="picker">
      <label>
        Universities
        <input
          value={query}
          onFocus={() => setActive(true)}
          onChange={(e) => {
            setActive(true);
            setQuery(e.target.value);
          }}
          placeholder="Search anywhere in the world…"
        />
      </label>
      {query.trim() && (
        <div className="suggestions">
          {results.map((item, i) => (
            <button
              type="button"
              key={item.name + i}
              onClick={() => pick(item)}
            >
              {item.name}
              <small>{item.country}</small>
            </button>
          ))}
          <button
            type="button"
            onClick={() => pick({ name: query.trim(), country: null })}
          >
            + Add “{query.trim()}”
          </button>
        </div>
      )}
      {error && <small>{error}</small>}
    </div>
  );
}
