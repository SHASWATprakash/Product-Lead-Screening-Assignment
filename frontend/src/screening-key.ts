const storageKey = (tenantId: string, productId: string) => `lotwise-screening-key:${tenantId}:${productId}`;

export const screeningKeys = {
  getOrCreate(tenantId: string, productId: string) {
    const key = storageKey(tenantId, productId);
    const existing = sessionStorage.getItem(key);
    if (existing) return existing;
    const value = crypto.randomUUID?.() ?? `lotwise-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    sessionStorage.setItem(key, value);
    return value;
  },
  clear(tenantId: string, productId: string) {
    sessionStorage.removeItem(storageKey(tenantId, productId));
  },
};
