"use client";
import { useEffect, useState } from "react";
import type { Comparison } from "@/features/sessions/types";
import { post, patch, remove, request } from "@/lib/api";
import { UniversityPicker } from "@/features/universities/UniversityPicker";
import { Modal } from "@/components/Modal";
import { ResultCell } from "./ResultCell";
export function ComparisonView({
  comparison,
  onChange,
}: {
  comparison: Comparison;
  onChange: (value: Comparison) => void;
}) {
  const [error, setError] = useState("");
  const [adding, setAdding] = useState<"university" | "column" | null>(null);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const base = "/chats/" + comparison.id;
  const cells = comparison.colleges.flatMap((row) => row.cells);
  const running = cells.some((cell) =>
    ["queued", "running"].includes(cell.status),
  );
  const completed = cells.filter((cell) => cell.status === "completed").length;
  useEffect(() => {
    if (!running) return;
    let active = true;
    const timer = setInterval(() => {
      request<Comparison>(base)
        .then((v) => {
          if (active) onChange(v);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    }, 2500);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [base, running, onChange]);
  async function mutate(action: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await action();
      onChange(await request<Comparison>(base));
      setAdding(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="comparison">
      <header className="page-header">
        <div>
          <p className="eyebrow">YOUR RESEARCH SPACE</p>
          <input
            className="session-title"
            aria-label="Session title"
            maxLength={255}
            defaultValue={comparison.title}
            onBlur={(e) => {
              if (e.target.value.trim() !== comparison.title)
                void mutate(() =>
                  patch(base, { title: e.target.value.trim() }),
                );
            }}
          />
          <p className="muted">
            {comparison.colleges.length} universities ·{" "}
            {comparison.columns.length} questions · {completed} answers
          </p>
        </div>
        <button
          className="primary"
          disabled={
            busy ||
            running ||
            !comparison.colleges.length ||
            !comparison.columns.length
          }
          onClick={() => mutate(() => post(base + "/research"))}
        >
          {running ? "Researching…" : "✧ Research / retry"}
        </button>
      </header>
      <div className="glass workspace">
        <div className="toolbar">
          <label>
            Shared major
            <input
              maxLength={255}
              key={comparison.major}
              defaultValue={comparison.major ?? ""}
              placeholder="Any major"
              onBlur={(e) => {
                if (e.target.value !== (comparison.major ?? ""))
                  void mutate(() =>
                    patch(base, { major: e.target.value || null }),
                  );
              }}
            />
          </label>
          <div>
            <button onClick={() => setAdding("university")}>
              + University
            </button>
            <button onClick={() => setAdding("column")}>+ Question</button>
          </div>
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>UNIVERSITY</th>
                {comparison.columns.map((column) => (
                  <th key={column.id}>
                    <span>{column.label}</span>
                    <button
                      aria-label={"Remove " + column.label}
                      disabled={busy}
                      onClick={() =>
                        mutate(() => remove(base + "/columns/" + column.id))
                      }
                    >
                      ×
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparison.colleges.map((row) => (
                <tr key={row.id}>
                  <td>
                    <strong>{row.name}</strong>
                    <small>{row.country || "Custom university"}</small>
                    <input
                      aria-label={"Major for " + row.name}
                      maxLength={255}
                      key={row.major_override}
                      defaultValue={row.major_override ?? ""}
                      placeholder={
                        comparison.major || "Specific major (optional)"
                      }
                      onBlur={(e) => {
                        if (e.target.value !== (row.major_override ?? ""))
                          void mutate(() =>
                            patch(base + "/colleges/" + row.id, {
                              major_override: e.target.value || null,
                            }),
                          );
                      }}
                    />
                    <button
                      className="text-button"
                      disabled={busy}
                      onClick={() =>
                        mutate(() => remove(base + "/colleges/" + row.id))
                      }
                    >
                      Remove university
                    </button>
                  </td>
                  {comparison.columns.map((column) => (
                    <td key={column.id}>
                      <ResultCell
                        cell={row.cells.find(
                          (cell) => cell.column_id === column.id,
                        )}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {!comparison.colleges.length && (
            <div className="table-empty">
              Your shortlist starts here.
              <p>Add a university to explore your possibilities.</p>
              <button onClick={() => setAdding("university")}>
                + Add university
              </button>
            </div>
          )}
        </div>
        <div className="table-foot">
          <span>✧ Source links included when available</span>
          <span>Always verify current requirements with the university.</span>
        </div>
      </div>
      {adding && (
        <Modal
          title={
            adding === "university" ? "Add university" : "Ask a new question"
          }
          onClose={() => setAdding(null)}
        >
          {adding === "university" ? (
            <UniversityPicker
              onAdd={(item) => {
                void mutate(() => post(base + "/colleges", item));
              }}
            />
          ) : (
            <>
              <label>
                Comparison question
                <input
                  maxLength={255}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Scholarships for international students"
                />
              </label>
              <button
                className="primary"
                disabled={busy || !question.trim()}
                onClick={() =>
                  mutate(() =>
                    post(base + "/columns", { label: question.trim() }),
                  )
                }
              >
                Add question
              </button>
            </>
          )}
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </Modal>
      )}
    </section>
  );
}
