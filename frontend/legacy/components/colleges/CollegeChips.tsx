"use client";

import type { CollegeSearchResult } from "@/lib/types";

type Props = {
  colleges: CollegeSearchResult[];
  onRemove: (college: CollegeSearchResult) => void;
};

export function CollegeChips({ colleges, onRemove }: Props) {
  if (colleges.length === 0) return null;

  return (
    <ul className="mt-2 flex flex-wrap gap-1.5">
      {colleges.map((college) => (
        <li
          key={`${college.name}-${college.country}`}
          className="flex items-center gap-1 border border-neutral-200 px-2 py-0.5 text-xs"
        >
          {college.name}
          <button type="button" className="text-neutral-400" onClick={() => onRemove(college)}>
            ×
          </button>
        </li>
      ))}
    </ul>
  );
}
