"use client";
import { useState } from "react";
import { uploadImage } from "@/modules/orbit/api";

export default function AttachmentPanel({ onInsert }: { onInsert?: (url: string) => void }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function onPick(ev: React.ChangeEvent<HTMLInputElement>) {
    const f = ev.target.files?.[0];
    if (!f) return;
    setBusy(true);
    setMsg(null);
    try {
      const { url } = await uploadImage(f);
      onInsert?.(url);
      setMsg("已上传");
    } catch (e: any) {
      setMsg(e?.message || "上传失败");
    } finally {
      setBusy(false);
      ev.target.value = "";
    }
  }

  return (
    <div className="space-y-2">
      <div className="text-sm font-medium">Attachments</div>
      <input type="file" accept="image/*" onChange={onPick} disabled={busy} />
      {msg && <div className="text-xs text-gray-500">{msg}</div>}
      <button className="px-2 py-1 border rounded" onClick={() => onInsert?.("")} disabled={busy}>
        插入占位
      </button>
    </div>
  );
}