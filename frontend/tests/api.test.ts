import { afterEach, describe, expect, it, vi } from "vitest";
import { api, gapCount, isWriter, session, setUnauthorizedHandler } from "../src/api";
import { screeningKeys } from "../src/screening-key";
import { queryKeys } from "../src/query-keys";
import type { Me } from "../src/types";

describe("workspace helpers", () => {
  it("counts only explicit evidence gaps", () => {
    expect(gapCount({ fields: { complete: { gap: false }, unknown: { gap: true }, defaulted: { gap: false } } })).toBe(1);
  });

  it("uses API permissions rather than role names for mutations", () => {
    const viewer: Me = { user: { id: "usr", email: "viewer@example.com", name: "Viewer", title: "", role: "viewer", tenant_id: "tenant" }, tenant: { id: "tenant", name: "Tenant", plan: "", home_region: "" }, permissions: ["profiles:read"] };
    expect(isWriter(viewer, "profiles:write")).toBe(false);
    expect(isWriter({ ...viewer, permissions: ["profiles:read", "profiles:write"] }, "profiles:write")).toBe(true);
  });
});

describe("session safety", () => {
  afterEach(() => {
    session.clear();
    setUnauthorizedHandler(null);
    vi.unstubAllGlobals();
  });

  it("clears the stored session and notifies the app on an authenticated 401", async () => {
    const onUnauthorized = vi.fn();
    session.set("expired-token");
    setUnauthorizedHandler(onUnauthorized);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Invalid or expired token" }), { status: 401 })));

    await expect(api.me()).rejects.toMatchObject({ status: 401 });
    expect(session.get()).toBeNull();
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("preserves a valid session for a tenant-scoped 404", async () => {
    const onUnauthorized = vi.fn();
    session.set("valid-token");
    setUnauthorizedHandler(onUnauthorized);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Product not found" }), { status: 404 })));

    await expect(api.bundle("prd_not_visible")).rejects.toMatchObject({ status: 404, detail: "Product not found" });
    expect(session.get()).toBe("valid-token");
    expect(onUnauthorized).not.toHaveBeenCalled();
  });

  it("preserves aborts so abandoned routes do not become application errors", async () => {
    const controller = new AbortController();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new DOMException("The operation was aborted", "AbortError")));

    await expect(api.bundle("prd_granola", controller.signal)).rejects.toMatchObject({ name: "AbortError" });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/v1/products/prd_granola"), expect.objectContaining({ signal: controller.signal }));
  });
});

describe("screening idempotency", () => {
  afterEach(() => sessionStorage.clear());

  it("reuses a key for a retry within the same tenant and product only", () => {
    const initial = screeningKeys.getOrCreate("tnt_northwind", "prd_trail_bar");
    expect(screeningKeys.getOrCreate("tnt_northwind", "prd_trail_bar")).toBe(initial);
    expect(screeningKeys.getOrCreate("tnt_harbor", "prd_trail_bar")).not.toBe(initial);
    expect(screeningKeys.getOrCreate("tnt_northwind", "prd_granola")).not.toBe(initial);
  });
});

describe("tenant query isolation", () => {
  it("does not share cache keys across tenants", () => {
    expect(queryKeys.bundle("tnt_northwind", "prd_granola")).not.toEqual(queryKeys.bundle("tnt_harbor", "prd_granola"));
    expect(queryKeys.runs("tnt_northwind", "prd_granola")).not.toEqual(queryKeys.runs("tnt_harbor", "prd_granola"));
  });
});
