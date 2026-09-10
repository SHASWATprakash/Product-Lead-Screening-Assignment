export const queryKeys = {
  me: ["me"] as const,
  usage: (tenantId: string) => ["usage", tenantId] as const,
  products: (tenantId: string) => ["products", tenantId] as const,
  facilities: (tenantId: string) => ["facilities", tenantId] as const,
  bundle: (tenantId: string, productId: string) => ["bundle", tenantId, productId] as const,
  runs: (tenantId: string, productId: string) => ["runs", tenantId, productId] as const,
  run: (tenantId: string, runId: string) => ["run", tenantId, runId] as const,
};
