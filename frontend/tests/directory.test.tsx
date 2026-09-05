import { beforeEach, expect, it, vi } from "vitest";
import { request } from "@/lib/api";

vi.mock("@/lib/api", () => ({ request: vi.fn() }));
const rows = [
  { name: "Example University", country: "Canada" },
  { name: "Other Institute", country: "United States" },
];
beforeEach(() => {
  vi.resetModules();
  vi.clearAllMocks();
  sessionStorage.clear();
});

it("shares one download across concurrent and repeated searches", async () => {
  vi.mocked(request).mockResolvedValue(rows);
  const { loadDirectory, searchDirectory } =
    await import("@/features/universities/directory");
  const [first, second] = await Promise.all([loadDirectory(), loadDirectory()]);
  expect(first).toEqual(second);
  expect(searchDirectory(first, "example canada")).toEqual([rows[0]]);
  expect(searchDirectory(await loadDirectory(), "united")).toEqual([rows[1]]);
  expect(request).toHaveBeenCalledExactlyOnceWith("/colleges/directory");
});

it("reuses the stored directory after a module reload", async () => {
  vi.mocked(request).mockResolvedValue(rows);
  await (await import("@/features/universities/directory")).loadDirectory();
  vi.resetModules();
  expect(
    await (await import("@/features/universities/directory")).loadDirectory(),
  ).toEqual(rows);
  expect(request).toHaveBeenCalledTimes(1);
});

it("refreshes an expired cache", async () => {
  sessionStorage.setItem(
    "campuspath-university-directory-v1",
    JSON.stringify({ expires: 1, rows }),
  );
  vi.mocked(request).mockResolvedValue(rows);
  await (await import("@/features/universities/directory")).loadDirectory();
  expect(request).toHaveBeenCalledTimes(1);
});

it("can retry a failed download", async () => {
  vi.mocked(request)
    .mockRejectedValueOnce(new Error("Offline"))
    .mockResolvedValueOnce(rows);
  const { loadDirectory } = await import("@/features/universities/directory");
  await expect(loadDirectory()).rejects.toThrow("Offline");
  expect(await loadDirectory()).toEqual(rows);
});

it("limits results and ranks name prefixes first without changing the directory", async () => {
  const { searchDirectory } = await import("@/features/universities/directory");
  const directory = [
    { name: "Other Example", country: null },
    ...Array.from({ length: 20 }, (_, n) => ({
      name: `Example ${n}`,
      country: null,
    })),
  ];
  expect(searchDirectory(directory, "e")).toEqual([]);
  const matches = searchDirectory(directory, "EXAMPLE");
  expect(matches).toHaveLength(12);
  expect(matches[0].name).toMatch(/^Example/);
  expect(directory[0].name).toBe("Other Example");
});
