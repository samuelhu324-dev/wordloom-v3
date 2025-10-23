"use client";

import React, { useMemo, useState } from "react";
import { useTheme } from "@/providers/ThemeProvider";
import { useUserPrefs } from "@/providers/UserPreferenceProvider";
import { exportAppearance, importAppearance } from "@/lib/prefs";
import { buildPreviewUrl, parseAppearanceFlags } from "@/lib/appearanceUrl";

export default function ThemeToolbar({ compact = false, enableGestures = true }: { compact?: boolean; enableGestures?: boolean }) {
  const { theme, setTheme } = useTheme();
  const { prefs, update, reset } = useUserPrefs();
  const [open, setOpen] = useState(true);
  const flags = parseAppearanceFlags();

  const [touchStart, setTouchStart] = useState<number | null>(null);
  const onTouchStart = (e: React.TouchEvent) => enableGestures && setTouchStart(e.touches[0].clientY);
  const onTouchEnd = (e: React.TouchEvent) => {
    if (!enableGestures || touchStart == null) return;
    const delta = e.changedTouches[0].clientY - touchStart;
    if (delta <= -40) setOpen(false);
    if (delta >=  40) setOpen(true);
    setTouchStart(null);
  };

  const paletteItems = useMemo(() => ([
    { key: "sky",    label: "淡蓝",  swatch: "#5B8CFF" },
    { key: "indigo", label: "蓝紫",  swatch: "#5E60CE" },
    { key: "maroon", label: "酒红",  swatch: "#7B1E3A" },
  ] as const), []);

  const disabled = !!flags.readonly;

  const onExportLink = () => {
    const url = buildPreviewUrl(exportAppearance(), { readonly: true, allowImport: true });
    navigator.clipboard?.writeText(url);
    alert("已复制预览链接（只读，允许对方一键导入）");
  };

  const onImportFromPreview = () => {
    if (!flags.allowImport) return;
    importAppearance(exportAppearance());
    alert("已导入到本地偏好。");
  };

  const Panel = (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm">主题色：</span>
        {paletteItems.map(p => (
          <button key={p.key} disabled={disabled} onClick={() => setTheme(p.key as any)}
            className={`h-7 px-3 rounded-full border text-white text-sm ${theme===p.key?"opacity-100":"opacity-80"} ${disabled?"opacity-50 cursor-not-allowed":""}`}
            style={{ background: p.swatch, borderColor: "var(--border)" }}>
            {p.label}
          </button>
        ))}
        <button disabled={disabled} onClick={() => setTheme(theme === "dark" ? "light" : "dark")} className={`h-7 px-3 rounded-full border text-sm ${disabled?"opacity-50 cursor-not-allowed":""}`}>
          {theme === "dark" ? "切到亮色" : "切到暗色"}
        </button>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm">字体：</span>
        <button disabled={disabled} onClick={() => update({ fontFamily: "serif" })} className={`h-7 px-3 rounded border text-sm ${prefs.fontFamily==="serif"?"bg-[var(--muted)]/30":""}`}>衬线</button>
        <button disabled={disabled} onClick={() => update({ fontFamily: "sans" })}  className={`h-7 px-3 rounded border text-sm ${prefs.fontFamily==="sans"?"bg-[var(--muted)]/30":""}`}>无衬线</button>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm">字号：</span>
        <input disabled={disabled} type="range" min={14} max={22} step={1} value={prefs.baseSize} onChange={e => update({ baseSize: Number(e.target.value) })} />
        <span className="text-xs w-10">{prefs.baseSize}px</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm">行距：</span>
        <input disabled={disabled} type="range" min={1.2} max={2.0} step={0.05} value={prefs.lineHeight} onChange={e => update({ lineHeight: Number(e.target.value) })} />
        <span className="text-xs w-10">{prefs.lineHeight.toFixed(2)}</span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm">字间距：</span>
        <input disabled={disabled} type="range" min={-0.02} max={0.1} step={0.01} value={prefs.letterSpacing} onChange={e => update({ letterSpacing: Number(e.target.value) })} />
        <span className="text-xs w-16">{prefs.letterSpacing.toFixed(2)}em</span>
      </div>

      <div className="flex items-center gap-2">
        <button onClick={onExportLink} className="h-7 px-3 rounded border text-sm">复制只读预览链接</button>
        {flags.allowImport && (
          <button onClick={onImportFromPreview} className="h-7 px-3 rounded border text-sm">一键导入到本地</button>
        )}
        {flags.readonly && !flags.allowImport && <span className="text-xs" style={{color:"var(--muted)"}}>只读预览模式</span>}
      </div>

      <button disabled={disabled} onClick={reset} className={`self-end h-7 px-3 rounded border text-sm ${disabled?"opacity-50 cursor-not-allowed":""}`}>重置外观</button>
    </div>
  );

  const Wrapper = ({children}:{children:React.ReactNode}) => (
    <div className="transition-all duration-200 ease-in-out" onTouchStart={(e)=>enableGestures&&setTouchStart(e.touches[0].clientY)} onTouchEnd={onTouchEnd}>
      {children}
    </div>
  );

  if (compact) {
    return (
      <Wrapper>
        <div className="rounded-2xl border p-3" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">外观设置</div>
            <button className="text-xs px-2 py-1 border rounded" onClick={() => setOpen(s => !s)}>{open ? "收起" : "展开"}</button>
          </div>
          {open && <div className="mt-3">{Panel}</div>}
        </div>
      </Wrapper>
    );
  }

  return (
    <Wrapper>
      <div className="sticky top-0 z-30 mb-4 border-b transition-all duration-200 ease-in-out" style={{ background: "var(--card-bg)", borderColor: "var(--border)" }}>
        <div className="mx-auto max-w-5xl px-4 py-3 flex items-center gap-3">
          <button className="px-2 py-1 text-sm border rounded" onClick={() => setOpen(s => !s)}>
            外观设置 {open ? "▲" : "▼"}
          </button>
          <div className="ml-auto text-xs" style={{ color: "var(--muted)" }}>触控：上滑收起，下滑展开</div>
        </div>
        {open && <div className="mx-auto max-w-5xl px-4 pb-3">{Panel}</div>}
      </div>
    </Wrapper>
  );
}
