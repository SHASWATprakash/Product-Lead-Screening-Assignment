import { describe, expect, it } from "vitest";
import { gapCount, isWriter } from "../src/api";
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
