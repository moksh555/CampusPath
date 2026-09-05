import { beforeEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ComparisonView } from "@/features/comparison/ComparisonView";
import type { Comparison } from "@/features/sessions/types";
import { post, request } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  post: vi.fn(),
  request: vi.fn(),
  patch: vi.fn(),
  remove: vi.fn(),
}));
const fixture: Comparison = {
  id: "session",
  title: "My shortlist",
  major: "CS",
  columns: [{ id: "fees", label: "Annual fees", is_default: false }],
  colleges: [
    {
      id: "school",
      name: "Example University",
      country: "Canada",
      major_override: null,
      cells: [
        {
          id: "cell",
          column_id: "fees",
          status: "empty",
          value: "",
          sources: [],
          researched_at: null,
        },
      ],
    },
  ],
};
beforeEach(() => vi.clearAllMocks());

it("does not start research for an incomplete draft", () => {
  render(
    <ComparisonView
      comparison={{ ...fixture, colleges: [] }}
      onChange={() => {}}
    />,
  );
  expect(
    screen.getByRole("button", { name: /Research \/ retry/ }),
  ).toBeDisabled();
});

it("shows an actionable error when the agent endpoint is unconfigured", async () => {
  vi.mocked(post).mockRejectedValue(new Error("Configure AGENT_URL"));
  render(<ComparisonView comparison={fixture} onChange={() => {}} />);
  fireEvent.click(screen.getByRole("button", { name: /Research \/ retry/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Configure AGENT_URL",
  );
  expect(post).toHaveBeenCalledWith("/chats/session/research");
});

it("adds a natural-language question and reloads the saved comparison", async () => {
  vi.mocked(post).mockResolvedValue({});
  vi.mocked(request).mockResolvedValue(fixture);
  const changed = vi.fn();
  render(<ComparisonView comparison={fixture} onChange={changed} />);
  fireEvent.click(screen.getByRole("button", { name: "+ Question" }));
  fireEvent.change(screen.getByLabelText("Comparison question"), {
    target: { value: "STEM courses offered" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Add question" }));
  await waitFor(() => expect(changed).toHaveBeenCalledWith(fixture));
  expect(post).toHaveBeenCalledWith("/chats/session/columns", {
    label: "STEM courses offered",
  });
});
