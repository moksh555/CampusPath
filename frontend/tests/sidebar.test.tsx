import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { SessionDashboard } from "@/features/sessions/SessionDashboard";
import { remove, request } from "@/lib/api";
vi.mock("@/lib/api", () => ({
  request: vi.fn(),
  post: vi.fn(),
  remove: vi.fn(),
}));
beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  vi.mocked(request).mockImplementation(((path: string) =>
    Promise.resolve(
      path === "/auth/me" ? { name: "Ada" } : [],
    )) as typeof request);
});
describe("sidebar collapse", () => {
  it("remembers a collapsed sidebar", async () => {
    render(<SessionDashboard />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Collapse sidebar" }),
    );
    expect(localStorage.getItem("campuspath:sidebar")).toBe("collapsed");
    expect(
      screen.getByRole("button", { name: "Expand sidebar" }),
    ).toHaveAttribute("aria-expanded", "false");
    expect(document.querySelector("aside")).toHaveClass("collapsed");
  });
  it("restores the collapsed rail on load", async () => {
    localStorage.setItem("campuspath:sidebar", "collapsed");
    render(<SessionDashboard />);
    expect(
      await screen.findByRole("button", { name: "Expand sidebar" }),
    ).toBeInTheDocument();
    expect(document.querySelector("aside")).toHaveClass("collapsed");
  });
  it("expands again and clears the stored preference", async () => {
    localStorage.setItem("campuspath:sidebar", "collapsed");
    render(<SessionDashboard />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Expand sidebar" }),
    );
    expect(localStorage.getItem("campuspath:sidebar")).toBe("expanded");
    expect(document.querySelector("aside")).not.toHaveClass("collapsed");
  });
});
describe("session deletion", () => {
  beforeEach(() => {
    vi.mocked(request).mockImplementation(((path: string) =>
      Promise.resolve(
        path === "/auth/me"
          ? { name: "Ada" }
          : [{ id: "s1", title: "My shortlist", major: "CS" }],
      )) as typeof request);
  });
  it("confirms in-app instead of using a browser popup", async () => {
    render(<SessionDashboard />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Delete My shortlist" }),
    );
    expect(
      await screen.findByText(/will be permanently deleted/),
    ).toBeInTheDocument();
    expect(remove).not.toHaveBeenCalled();
  });
  it("keeps the session when cancelled", async () => {
    render(<SessionDashboard />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Delete My shortlist" }),
    );
    const dialog = within(await screen.findByRole("dialog"));
    fireEvent.click(dialog.getByRole("button", { name: "Cancel" }));
    expect(remove).not.toHaveBeenCalled();
    expect(screen.getByText("My shortlist")).toBeInTheDocument();
  });
  it("deletes the session when confirmed", async () => {
    render(<SessionDashboard />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Delete My shortlist" }),
    );
    const dialog = within(await screen.findByRole("dialog"));
    fireEvent.click(dialog.getByRole("button", { name: "Delete session" }));
    await waitFor(() => expect(remove).toHaveBeenCalledWith("/chats/s1"));
    await waitFor(() =>
      expect(screen.queryByText("My shortlist")).not.toBeInTheDocument(),
    );
  });
});
