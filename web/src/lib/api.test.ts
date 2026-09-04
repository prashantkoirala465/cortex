import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, withAuth } from "@/lib/api";

describe("apiFetch", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed json on success", async () => {
    global.fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ hello: "world" }), { status: 200 }));
    await expect(apiFetch("/whatever")).resolves.toEqual({ hello: "world" });
  });

  it("returns null for 204 responses", async () => {
    global.fetch = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    await expect(apiFetch("/whatever")).resolves.toBeNull();
  });

  it("throws an ApiError with the parsed detail on failure", async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ detail: "not found" }), { status: 404 }));
    await expect(apiFetch("/whatever")).rejects.toMatchObject({ status: 404, detail: "not found" });
  });

  it("sends credentials and a json content-type by default", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("null", { status: 200 }));
    global.fetch = fetchMock;

    await apiFetch("/notes", { method: "POST", body: "{}" });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/notes"),
      expect.objectContaining({
        credentials: "include",
        method: "POST",
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      }),
    );
  });
});

describe("withAuth", () => {
  it("returns an authorization header when a token is given", () => {
    expect(withAuth("abc")).toEqual({ Authorization: "Bearer abc" });
  });

  it("returns an empty object when there is no token", () => {
    expect(withAuth(null)).toEqual({});
  });
});
