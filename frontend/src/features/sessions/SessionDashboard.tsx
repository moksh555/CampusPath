"use client";
import { useEffect, useState, useCallback, useRef } from "react";
import { request, post, remove } from "@/lib/api";
import { Login } from "@/features/auth/Login";
import { ComparisonView } from "@/features/comparison/ComparisonView";
import { NewSession } from "./NewSession";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import type { Comparison, Summary } from "./types";
export function SessionDashboard() {
  const [user, setUser] = useState<{ name: string } | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [sessions, setSessions] = useState<Summary[]>([]);
  const [active, setActive] = useState<Comparison | null>(null);
  const [create, setCreate] = useState(false);
  const [error, setError] = useState("");
  const [pendingDelete, setPendingDelete] = useState<Summary | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [collapsed, setCollapsed] = useState(
    () =>
      typeof window !== "undefined" &&
      window.localStorage.getItem("campuspath:sidebar") === "collapsed",
  );
  const selection = useRef(0);
  useEffect(() => {
    window.localStorage.setItem(
      "campuspath:sidebar",
      collapsed ? "collapsed" : "expanded",
    );
  }, [collapsed]);
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
  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await remove("/chats/" + pendingDelete.id);
      selection.current += 1;
      setSessions((v) => v.filter((s) => s.id !== pendingDelete.id));
      setActive((current) =>
        current?.id === pendingDelete.id ? null : current,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDeleting(false);
      setPendingDelete(null);
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
      <aside className={"sidebar glass" + (collapsed ? " collapsed" : "")}>
        <div className="sidebar-head">
          <a className="wordmark" href="/">
            <span className="brand-mark">C</span>
            <span className="wordmark-text">CampusPath</span>
          </a>
          <button
            className="sidebar-toggle"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            onClick={() => setCollapsed((value) => !value)}
          >
            {collapsed ? "»" : "«"}
          </button>
        </div>
        <button
          className="new-session"
          title="New session"
          onClick={() => setCreate(true)}
        >
          ＋ <span className="label">New session</span>
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
              <button title={session.title} onClick={() => open(session.id)}>
                ◈ <span>{session.title}</span>
              </button>
              <button
                aria-label={"Delete " + session.title}
                onClick={() => setPendingDelete(session)}
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
      {pendingDelete && (
        <ConfirmDialog
          title="Delete session"
          message={`“${pendingDelete.title}” and all of its researched answers will be permanently deleted.`}
          confirmLabel="Delete session"
          busy={deleting}
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </div>
  );
}
