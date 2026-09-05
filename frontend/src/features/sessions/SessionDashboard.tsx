"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import { request, post, remove } from "@/lib/api";
import { Login } from "@/features/auth/Login";
import { ComparisonView } from "@/features/comparison/ComparisonView";
import { NewSession } from "./NewSession";
import type { Comparison, Summary } from "./types";
export function SessionDashboard() {
  const [user, setUser] = useState<{ name: string } | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [sessions, setSessions] = useState<Summary[]>([]);
  const [active, setActive] = useState<Comparison | null>(null);
  const [create, setCreate] = useState(false);
  const [error, setError] = useState("");
  const selection = useRef(0);
  useEffect(() => {
    request<{ name: string }>("/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setLoaded(true));
  }, []);
  useEffect(() => {
    if (user)
      request<Summary[]>("/chats")
        .then(setSessions)
        .catch((e) => setError(e.message));
  }, [user]);
  const change = useCallback((value: Comparison) => {
    setActive((current) => (current?.id === value.id ? value : current));
    setSessions((items) =>
      items.map((item) => (item.id === value.id ? value : item)),
    );
  }, []);
  async function open(id: string) {
    const requestId = ++selection.current;
    setError("");
    try {
      const result = await request<Comparison>("/chats/" + id);
      if (requestId === selection.current) setActive(result);
    } catch (e) {
      if (requestId === selection.current) setError((e as Error).message);
    }
  }
  if (!loaded)
    return (
      <main className="login">
        <p>Opening your workspace…</p>
      </main>
    );
  if (!user) return <Login />;
  return (
    <div className="app-shell">
      <aside className="sidebar glass">
        <a className="wordmark" href="/">
          <span className="brand-mark">C</span>CampusPath
        </a>
        <button className="new-session" onClick={() => setCreate(true)}>
          ＋ New session
        </button>
        <p className="eyebrow">
          YOUR SESSIONS <span>{sessions.length}</span>
        </p>
        <nav>
          {sessions.map((session) => (
            <div
              className={
                "session-link " + (active?.id === session.id ? "selected" : "")
              }
              key={session.id}
            >
              <button onClick={() => open(session.id)}>
                ◈ <span>{session.title}</span>
              </button>
              <button
                aria-label={"Delete " + session.title}
                onClick={async () => {
                  if (!window.confirm("Delete this comparison session?"))
                    return;
                  try {
                    await remove("/chats/" + session.id);
                    selection.current += 1;
                    setSessions((v) => v.filter((s) => s.id !== session.id));
                    setActive((current) =>
                      current?.id === session.id ? null : current,
                    );
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                ×
              </button>
            </div>
          ))}
        </nav>
        <div className="profile">
          <div className="avatar">{user.name[0]}</div>
          <span>
            {user.name}
            <small>Personal workspace</small>
          </span>
          <button
            aria-label="Sign out"
            onClick={async () => {
              try {
                await post("/auth/logout");
                selection.current += 1;
                setUser(null);
                setCreate(false);
                setActive(null);
                setSessions([]);
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            ↗
          </button>
        </div>
      </aside>
      <main className="main-space">
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {active ? (
          <ComparisonView
            key={active.id}
            comparison={active}
            onChange={change}
          />
        ) : (
          <section className="welcome">
            <p className="eyebrow">A WORLD OF POSSIBILITIES</p>
            <h1>
              Big decisions.
              <br />
              <span>Clearer perspectives.</span>
            </h1>
            <p>
              Bring your universities together.
              <br />
              Compare what matters to you, one question at a time.
            </p>
            <button className="primary" onClick={() => setCreate(true)}>
              Create your first session ↗
            </button>
            <div className="welcome-cards">
              <article className="glass">
                <b>01</b>
                <h3>Build your shortlist</h3>
                <p>
                  Universities from anywhere.
                  <br />
                  Your future has no borders.
                </p>
              </article>
              <article className="glass">
                <b>02</b>
                <h3>Ask your questions</h3>
                <p>
                  Fees, courses, opportunities.
                  <br />
                  You choose what matters.
                </p>
              </article>
              <article className="glass">
                <b>03</b>
                <h3>See the whole picture</h3>
                <p>
                  Research with source links.
                  <br />
                  Compare with confidence.
                </p>
              </article>
            </div>
          </section>
        )}
      </main>
      {create && (
        <NewSession
          onClose={() => setCreate(false)}
          onCreate={(value) => {
            selection.current += 1;
            setSessions((v) => [value, ...v]);
            setActive(value);
            setCreate(false);
          }}
        />
      )}
    </div>
  );
}
