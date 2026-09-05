export type CellStatus = "empty" | "loading" | "filled" | "error";

/** One college x column intersection. Empty until the agent pass fills it. */
export type Cell = {
  id: string;
  column_id: string;
  value: string;
  status: CellStatus;
};

/** A row in the comparison table. */
export type College = {
  id: string;
  name: string;
  country: string | null;
  /** Overrides the chat-wide major for this college only. */
  major_override: string | null;
  cells: Cell[];
};

export type Column = {
  id: string;
  key: string;
  label: string;
  is_default: boolean;
  sort_order: number;
};

export type ChatSummary = {
  id: string;
  title: string;
  major: string | null;
  created_at: string;
};

export type ChatDetail = ChatSummary & {
  colleges: College[];
  columns: Column[];
};

/** A directory hit, not yet saved to a chat. */
export type CollegeSearchResult = {
  name: string;
  country: string | null;
};
