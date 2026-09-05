import type { Cell } from "@/features/sessions/types";
export function ResultCell({ cell }: { cell?: Cell }) {
  if (!cell) return <span className="muted">Not researched</span>;
  const waiting = ["queued", "running"].includes(cell.status);
  return (
    <div className="result">
      {cell.status !== "completed" && (
        <span className={"status " + (waiting ? "working" : "")}>
          {cell.status === "empty" ? "Not researched" : cell.status}
        </span>
      )}
      {cell.value && <p>{cell.value}</p>}
      {cell.status === "completed" && !cell.sources?.length && (
        <small>No source links returned</small>
      )}
      {cell.sources?.length > 0 && (
        <div className="sources">
          {cell.sources.map((source, i) =>
            /^https?:\/\//.test(source.url) ? (
              <a
                key={i}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                ↗ {source.title || new URL(source.url).hostname}
              </a>
            ) : null,
          )}
        </div>
      )}
      {cell.researched_at && (
        <small>
          Checked {new Date(cell.researched_at).toLocaleDateString()}
        </small>
      )}
    </div>
  );
}
