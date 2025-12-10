export function normalizeEntry(raw: any) {
  const id = raw?.id ?? raw?.entry_id ?? "";
  const src = raw?.text ?? raw?.src ?? raw?.en ?? raw?.en_text ?? "";
  const tgt = raw?.translation ?? raw?.tgt ?? raw?.zh ?? raw?.zh_text ?? "";
  return {
    id,
    text: String(src ?? ""),
    translation: String(tgt ?? ""),
    source_name: String((raw?.source_name ?? raw?.source ?? "") || ""),
    created_at: String((raw?.created_at ?? raw?.ts_iso ?? "") || ""),
  };
}

export function normalizeSource(raw: any) {
  if (typeof raw === "string") return { name: raw };
  return {
    id: raw?.id ?? raw?.source_id,
    name: raw?.name ?? raw?.source_name ?? String(raw?.id ?? ""),
  };
}
