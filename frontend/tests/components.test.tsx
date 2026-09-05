import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { NewSession } from "@/features/sessions/NewSession";
import { ResultCell } from "@/features/comparison/ResultCell";
import { Login } from "@/features/auth/Login";
import { UniversityPicker } from "@/features/universities/UniversityPicker";
import { post, request } from "@/lib/api";
vi.mock("@/lib/api", () => ({ post: vi.fn(), request: vi.fn() }));
beforeEach(() => vi.clearAllMocks());
describe("session setup", () => {
  it("saves a draft with editable natural-language columns", async () => {
    vi.mocked(post).mockResolvedValue({ id: "1" });
    const created = vi.fn();
    render(<NewSession onClose={() => {}} onCreate={created} />);
    fireEvent.change(screen.getByLabelText("Custom comparison question"), {
      target: { value: "STEM courses offered" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^Add$/ }));
    fireEvent.click(screen.getByRole("button", { name: "Create session →" }));
    await waitFor(() => expect(created).toHaveBeenCalled());
    expect(post).toHaveBeenCalledWith(
      "/chats",
      expect.objectContaining({
        columns: expect.arrayContaining(["STEM courses offered"]),
      }),
    );
  });
  it("shows a recoverable server error", async () => {
    vi.mocked(post).mockRejectedValue(new Error("Could not save"));
    render(<NewSession onClose={() => {}} onCreate={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Create session →" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not save",
    );
    expect(
      screen.getByRole("button", { name: "Create session →" }),
    ).toBeEnabled();
  });
  it("allows custom universities without waiting for directory", async () => {
    vi.mocked(request).mockRejectedValueOnce(new Error("Offline"));
    const add = vi.fn();
    render(<UniversityPicker onAdd={add} />);
    fireEvent.change(
      screen.getByPlaceholderText("Search anywhere in the world…"),
      { target: { value: "Local Institute" } },
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: "＋ Add “Local Institute”".replace("＋", "+"),
      }),
    );
    expect(add).toHaveBeenCalledWith({
      name: "Local Institute",
      country: null,
    });
    expect(await screen.findByText("Directory unavailable. You can still add this university by name.")).toBeInTheDocument();
  });
});
describe("result rendering", () => {
  it("renders pending state", () => {
    render(<ResultCell />);
    expect(screen.getByText("Not researched")).toBeInTheDocument();
  });
  it("renders answer and sources without interpreting answer HTML", () => {
    render(
      <ResultCell
        cell={{
          id: "1",
          column_id: "2",
          status: "completed",
          value: "<script>bad</script>",
          sources: [
            { title: "Official fees", url: "https://example.edu/fees" },
          ],
          researched_at: null,
        }}
      />,
    );
    expect(screen.getByText("<script>bad</script>")).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );
  });
  it("does not make unsafe source URLs clickable", () => {
    render(
      <ResultCell
        cell={{
          id: "1",
          column_id: "2",
          status: "completed",
          value: "Answer",
          sources: [{ title: "Unsafe", url: "javascript:alert(1)" }],
          researched_at: null,
        }}
      />,
    );
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
it("offers Google as the only sign-in method", () => {
  render(<Login />);
  expect(
    screen.getByRole("link", { name: /Continue with Google/ }),
  ).toHaveAttribute("href", "http://localhost:8000/auth/login");
  expect(screen.queryByRole("textbox")).toBeNull();
});

it("loads the directory on focus and searches locally while typing", async () => {
  vi.mocked(request).mockResolvedValue([
    { name: "Example University", country: "Canada" },
    { name: "Other Institute", country: "France" },
  ]);
  render(<UniversityPicker onAdd={() => {}} />);
  const input = screen.getByLabelText("Universities");
  expect(request).not.toHaveBeenCalled();
  fireEvent.focus(input);
  fireEvent.change(input, { target: { value: "example" } });
  expect(await screen.findByRole("button", { name: "Example University Canada" })).toBeInTheDocument();
  fireEvent.change(input, { target: { value: "france" } });
  expect(await screen.findByRole("button", { name: "Other Institute France" })).toBeInTheDocument();
  expect(request).toHaveBeenCalledExactlyOnceWith("/colleges/directory");
});
