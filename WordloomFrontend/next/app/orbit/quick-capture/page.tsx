"use client";
import { useEffect, useState } from "react";
import { quickCapture } from "@/modules/orbit/api";

export default function QuickCapturePage() {
  const [title, setTitle] = useState(""); const [url, setUrl] = useState("");
  const [selection, setSelection] = useState(""); const [tags, setTags] = useState("");
  const [busy, setBusy] = useState(false); const [msg, setMsg] = useState<string | null>(null);

  useEffect(()=>{ const sp=new URLSearchParams(location.search);
    sp.get("title")&&setTitle(sp.get("title")!);
    sp.get("url")&&setUrl(sp.get("url")!);
    sp.get("selection")&&setSelection(sp.get("selection")!);
    sp.get("tags")&&setTags(sp.get("tags")!);
  },[]);

  async function onSubmit(){ setBusy(true); setMsg(null);
    try{
      const note = await quickCapture({
        title: title||undefined, url: url||undefined, selection: selection||undefined,
        tags: tags?tags.split(",").map(s=>s.trim()).filter(Boolean):undefined,
      });
      setMsg(`已创建：#${note.id.slice(0,8)}`);
    }catch(e:any){ setMsg(e?.message||"创建失败"); } finally{ setBusy(false); }
  }

  return (
    <main className="max-w-xl mx-auto px-5 py-6 space-y-3">
      <h1 className="text-xl font-semibold">Quick Capture</h1>
      <input className="w-full rounded border p-2" placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} />
      <input className="w-full rounded border p-2" placeholder="URL" value={url} onChange={e=>setUrl(e.target.value)} />
      <textarea className="w-full min-h-40 border rounded p-3 text-sm" placeholder="Selection / Content" value={selection} onChange={e=>setSelection(e.target.value)} />
      <input className="w-full rounded border p-2" placeholder="tags, comma,separated" value={tags} onChange={e=>setTags(e.target.value)} />
      <div className="flex gap-2">
        <button className="px-3 py-2 bg-blue-600 text-white rounded" onClick={onSubmit} disabled={busy}>提交</button>
        {msg && <div className="text-sm text-gray-500">{msg}</div>}
      </div>
    </main>
  );
}