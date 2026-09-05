"use client";
import { useState } from "react";
import { Modal } from "@/components/Modal";
import { UniversityPicker } from "@/features/universities/UniversityPicker";
import type { Comparison, University } from "./types";
import { post } from "@/lib/api";
const defaults = [
  "Annual tuition fees",
  "Admission prerequisites",
  "Location",
  "Course overview",
];
export function NewSession({
  onClose,
  onCreate,
}: {
  onClose: () => void;
  onCreate: (value: Comparison) => void;
}) {
  const [universities, setUniversities] = useState<University[]>([]);
  const [columns, setColumns] = useState(defaults);
  const [question, setQuestion] = useState("");
  const [major, setMajor] = useState("");
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function save() {
    setBusy(true);
    setError("");
    try {
      onCreate(
        await post<Comparison>("/chats", {
          title,
          major,
          colleges: universities,
          columns,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="A new possibility" onClose={onClose}>
      <p className="muted">
        Choose your universities and the questions you want answered.
      </p>
      <label>
        Session name
        <input
          maxLength={255}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="My graduate school shortlist"
        />
      </label>
      <UniversityPicker
        onAdd={(item) =>
          setUniversities((v) =>
            v.some((x) => x.name === item.name && x.country === item.country)
              ? v
              : [...v, item],
          )
        }
      />
      <div className="chips">
        {universities.map((item, i) => (
          <button
            key={i}
            onClick={() => setUniversities((v) => v.filter((_, n) => n !== i))}
          >
            {item.name} ×
          </button>
        ))}
      </div>
      <label>
        Shared major <small>optional · can vary by university</small>
        <input
          maxLength={255}
          value={major}
          onChange={(e) => setMajor(e.target.value)}
          placeholder="e.g. Computer Science"
        />
      </label>
      <label>What would you like to compare?</label>
      <div className="chips">
        {columns.map((label, i) => (
          <button
            key={i}
            onClick={() => setColumns((v) => v.filter((_, n) => n !== i))}
          >
            {label} ×
          </button>
        ))}
      </div>
      <div className="inline">
        <input
          aria-label="Custom comparison question"
          maxLength={255}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. CS department world ranking"
          onKeyDown={(e) => {
            if (e.key === "Enter" && question.trim()) {
              setColumns((v) => [...v, question.trim()]);
              setQuestion("");
            }
          }}
        />
        <button
          disabled={!question.trim()}
          onClick={() => {
            setColumns((v) => [...v, question.trim()]);
            setQuestion("");
          }}
        >
          Add
        </button>
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <footer>
        <small>You can save a draft and add more later.</small>
        <button className="primary" disabled={busy} onClick={save}>
          {busy ? "Saving…" : "Create session →"}
        </button>
      </footer>
    </Modal>
  );
}
