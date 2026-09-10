import type { AgentResult, Bundle, ExtractResult, Facility, Ingredient, Me, Permission, Product, Run, Usage, User } from "./types";

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public detail: string) { super(detail); this.name = "ApiError"; }
}

let token: string | null = localStorage.getItem("lotwise-token");
export const session = { get: () => token, set: (value: string) => { token = value; localStorage.setItem("lotwise-token", value); }, clear: () => { token = null; localStorage.removeItem("lotwise-token"); } };
let unauthorizedHandler: (() => void) | null = null;
export const setUnauthorizedHandler = (handler: (() => void) | null) => { unauthorizedHandler = handler; };

async function request<T>(path: string, init: RequestInit = {}, auth = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (auth && token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try { response = await fetch(`${baseUrl}${path}`, { ...init, headers }); }
  catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "Could not reach the Lotwise Core API. Confirm it is running at the configured URL.");
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    if (auth && response.status === 401) {
      session.clear();
      unauthorizedHandler?.();
    }
    throw new ApiError(response.status, typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  demoUsers: () => request<{ users: (User & { tenant_name: string })[] }>("/v1/meta/demo-users", {}, false),
  token: async (email: string) => { const result = await request<{ access_token: string }>("/v1/auth/token", { method: "POST", body: JSON.stringify({ email }) }, false); session.set(result.access_token); return result; },
  me: () => request<Me>("/v1/me"), usage: () => request<Usage>("/v1/usage"),
  products: (signal?: AbortSignal) => request<{ items: Product[] }>("/v1/products", { signal }), facilities: (signal?: AbortSignal) => request<{ items: Facility[] }>("/v1/facilities", { signal }),
  bundle: (id: string, signal?: AbortSignal) => request<Bundle>(`/v1/products/${id}`, { signal }), runs: (id: string, signal?: AbortSignal) => request<{ items: Run[] }>(`/v1/screenings?product_id=${id}`, { signal }), run: (id: string, signal?: AbortSignal) => request<Run>(`/v1/screenings/${id}`, { signal }),
  generate: (product_id: string, key: string) => request<{ run_id: string; status: string }>("/v1/screenings:generate", { method: "POST", headers: { "Idempotency-Key": key }, body: JSON.stringify({ product_id }) }),
  patch: (target: "product" | "facility" | "ingredient", id: string, fields: Record<string, { value: unknown; source: string; tier?: string }>) => request<EntityResponse>(`/v1/${target === "facility" ? "facilities" : `${target}s`}/${id}`, { method: "PATCH", body: JSON.stringify({ fields }) }),
  notes: () => request<Record<string, string>>("/v1/meta/sample-notes", {}, false),
  extract: (notes: string, product_id: string, apply: boolean) => request<ExtractResult>("/v1/extract", { method: "POST", body: JSON.stringify({ notes, product_id, apply }) }),
  ask: (question: string, product_id: string) => request<AgentResult>("/v1/agent:ask", { method: "POST", body: JSON.stringify({ question, product_id }) }),
};
type EntityResponse = Product | Facility | Ingredient;
export const isWriter = (me: Me | undefined, permission: Permission) => Boolean(me?.permissions.includes(permission));
export const gapCount = (entity: { fields: Record<string, { gap: boolean }> }) => Object.values(entity.fields).filter((field) => field.gap).length;
