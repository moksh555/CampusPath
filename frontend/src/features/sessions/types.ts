export type University = { name: string; country: string | null };
export type Cell = {
  id: string;
  column_id: string;
  status: string;
  value: string;
  sources: { title: string; url: string }[];
  researched_at: string | null;
};
export type Row = University & {
  id: string;
  major_override: string | null;
  cells: Cell[];
};
export type Column = { id: string; label: string; is_default: boolean };
export type Summary = { id: string; title: string; major: string | null };
export type Comparison = Summary & { colleges: Row[]; columns: Column[] };
