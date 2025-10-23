"use client";

import React, { useEffect, useMemo, useState } from "react";
import ThemeToolbar from "@/components/common/ThemeToolbar";
import { useTheme } from "@/providers/ThemeProvider";
import { useUserPrefs } from "@/providers/UserPreferenceProvider";
import { exportAppearance, importAppearance } from "@/lib/prefs";
import { buildPreviewUrl, applyAppearanceFromUrl } from "@/lib/appearanceUrl";
import Link from "next/link";

// —— 保留你的本地预设机制 ——
const KEY_PRESETS = "wl_theme_presets";

type Preset = {
  id: string;
  name: string;
  thumb: string; // data URL (SVG)
  data: ReturnType<typeof exportAppearance>;
};

function svgThumb(accent:string) {
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='160' height='96'><rect width='100%' height='100%' fill='white'/><rect x='0' y='0' width='100%' height='24' fill='${accent}'/><rect x='12' y='44' width='136' height='8' rx='4' fill='#d1d5db'/><rect x='12' y='60' width='96' height='8' rx='4' fill='#9ca3af'/></svg>`;
  return "data:image/svg+xml;base64," + (typeof btoa !== "undefined" ? btoa(svg) : Buffer.from(svg).toString("base64"));
}

export default function ThemePage() {
  // ① 首屏允许从 URL 导入外观（你原有逻辑保留）
  useEffect(() => { applyAppearanceFromUrl(); }, []);

  const { theme, setTheme } = useTheme();
  const { prefs } = useUserPrefs();

  const [previewUrl, setPreviewUrl] = useState("");
  const [presets, setPresets] = useState<Preset[]>(() => {
    if (typeof window === "undefined") return [];
    try { return JSON.parse(localStorage.getItem(KEY_PRESETS) || "[]"); } catch { return []; }
  });
  const [name, setName] = useState("未命名主题");

  // ② 一键生成预览链接（只读 + 可导入）
  const makePreviewUrl = () => {
    const data = exportAppearance();
    setPreviewUrl(buildPreviewUrl(data, { readonly: true, allowImport: true }));
  };

  // ③ 保存为我的预设（保留你的逻辑）
  const savePreset = () => {
    const data = exportAppearance();
    const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#5B8CFF";
    const p: Preset = {
      id: String(Date.now()),
      name: name || "未命名主题",
      thumb: svgThumb(accent),
      data,
    };
    const next = [p, ...presets].slice(0, 20);
    setPresets(next);
    localStorage.setItem(KEY_PRESETS, JSON.stringify(next));
  };

  const applyPreset = (p: Preset) => {
    importAppearance(p.data);
    if (p.data.theme) setTheme(p.data.theme as any);
  };

  const sharePreset = async (p: Preset) => {
    const url = buildPreviewUrl(p.data, { readonly: true, allowImport: true });
    try { await navigator.clipboard?.writeText(url); } catch {}
    alert("已复制分享链接");
  };

  // —— 新增：可收起的“快速主题”面板（响应式） ——
  const [openQuick, setOpenQuick] = useState(true);
  const themeChips: {key:"sky"|"indigo"|"maroon"|"system"; label:string; dot:string}[] = [
    { key:"sky",    label:"sky",    dot:"#7CB8FF" },
    { key:"indigo", label:"indigo", dot:"#6366F1" },
    { key:"maroon", label:"maroon", dot:"#8B1C31" },
    { key:"system", label:"system", dot:"#10B981" },
  ];

  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">主题与外观</h1>
        <Link href="/" className="text-sm underline">返回 Home</Link>
      </header>

      {/* 预览链接 */}
      <div className="rounded-xl border p-4 flex flex-wrap items-center gap-3"
           style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <button onClick={makePreviewUrl} className="h-8 px-3 rounded border text-sm"
                style={{ borderColor:"var(--border)" }}>
          生成只读预览链接
        </button>
        {!!previewUrl && (
          <>
            <a className="truncate max-w-full text-sm underline" href={previewUrl} target="_blank" rel="noreferrer">
              {previewUrl}
            </a>
            <button
              onClick={async()=>{ try{ await navigator.clipboard?.writeText(previewUrl);}catch{} }}
              className="h-8 px-3 rounded border text-sm"
              style={{ borderColor:"var(--border)" }}
            >
              复制
            </button>
          </>
        )}
        <button
          onClick={()=>applyAppearanceFromUrl()}
          className="h-8 px-3 rounded border text-sm"
          style={{ borderColor:"var(--border)" }}
          title="从当前 URL（?theme=...）读取并应用外观"
        >
          从当前链接导入
        </button>
        <span className="text-xs" style={{color:"var(--muted)"}}>链接允许对方一键导入，不覆盖对方现有设置。</span>
      </div>

      {/* 新增：可收起的快速主题选择 */}
      <div className="rounded-xl border" style={{ borderColor:"var(--border)", background:"var(--surface)" }}>
        <button
          onClick={()=>setOpenQuick(v=>!v)}
          className="w-full flex items-center justify-between px-4 py-3"
        >
          <span className="text-sm font-medium">快速主题</span>
          <span className="text-xs" style={{color:"var(--muted)"}}>{openQuick ? "收起" : "展开"}</span>
        </button>
        {openQuick && (
          <div className="px-4 pb-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {themeChips.map(t => (
              <button
                key={t.key}
                onClick={()=>setTheme(t.key as any)}
                className={`h-9 px-3 rounded-full border text-sm flex items-center gap-2 justify-center ${theme===t.key ? "ring-2" : ""}`}
                style={{ borderColor:"var(--border)" }}
                aria-pressed={theme===t.key}
              >
                <span className="inline-block w-2.5 h-2.5 rounded-full" style={{background:t.dot}} />
                {t.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 你的外观工具条（保持不变） */}
      <ThemeToolbar />

      {/* 保存/命名/分享：主题市场雏形（保持不变+细节微调） */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium">我的预设</h2>
        <div className="flex flex-wrap items-center gap-2">
          <input
            className="h-8 px-2 rounded border text-sm bg-[var(--surface)]"
            placeholder="主题名"
            value={name}
            onChange={e=>setName(e.target.value)}
            style={{ borderColor:"var(--border)", color:"var(--fg)" }}
          />
          <button onClick={savePreset} className="h-8 px-3 rounded border text-sm" style={{ borderColor:"var(--border)" }}>
            保存为预设
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {presets.map(p => (
            <div key={p.id} className="rounded-xl border p-3 flex gap-3 items-center"
                 style={{ borderColor: "var(--border)", background:"var(--surface)" }}>
              <img src={p.thumb} alt="" className="w-32 h-20 rounded border" style={{ borderColor:"var(--border)" }} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{p.name}</div>
                <div className="mt-2 flex gap-2">
                  <button onClick={()=>applyPreset(p)} className="h-7 px-3 rounded border text-sm" style={{ borderColor:"var(--border)" }}>
                    应用
                  </button>
                  <button onClick={()=>sharePreset(p)} className="h-7 px-3 rounded border text-sm" style={{ borderColor:"var(--border)" }}>
                    分享
                  </button>
                  <button
                    onClick={()=>{
                      const next = presets.filter(x=>x.id!==p.id);
                      setPresets(next);
                      localStorage.setItem(KEY_PRESETS, JSON.stringify(next));
                    }}
                    className="h-7 px-3 rounded border text-sm"
                    style={{ borderColor:"var(--border)" }}
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
