import { afterEach, expect, it, vi } from "vitest";
import { request } from "@/lib/api";

afterEach(() => vi.unstubAllGlobals());

it("routes login-session reads to auth and dashboard reads to platform", async () => {
  const fetch = vi.fn().mockImplementation(async () => new Response(JSON.stringify({}), {status: 200}));
  vi.stubGlobal("fetch", fetch);
  await request("/auth/me");
  await request("/chats");
  expect(fetch.mock.calls[0][0]).toBe("http://localhost:8001/auth/me");
  expect(fetch.mock.calls[1][0]).toBe("http://localhost:8000/chats");
});

it("refreshes with auth before retrying a platform request", async () => {
  const fetch = vi.fn()
    .mockResolvedValueOnce(new Response("{}", {status: 401}))
    .mockResolvedValueOnce(new Response("{}", {status: 200}))
    .mockResolvedValueOnce(new Response(JSON.stringify({id: "chat"}), {status: 200}));
  vi.stubGlobal("fetch", fetch);
  expect(await request("/chats/one")).toEqual({id: "chat"});
  expect(fetch.mock.calls.map(([url]) => url)).toEqual([
    "http://localhost:8000/chats/one", "http://localhost:8001/auth/refresh", "http://localhost:8000/chats/one",
  ]);
});
