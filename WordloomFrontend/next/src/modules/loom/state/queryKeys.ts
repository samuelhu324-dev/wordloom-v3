export const qk = {
  sources: ["loom","sources"] as const,
  search:  (k:string) => ["loom","search",k] as const,
};
