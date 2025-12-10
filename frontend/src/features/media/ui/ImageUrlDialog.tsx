"use client";

import { useState, useEffect } from "react";

type Props = {
  open: boolean;
  initialUrl?: string;
  onClose: () => void;
  onConfirm: (url: string) => void;
};

export default function ImageUrlDialog({ open, initialUrl, onClose, onConfirm }: Props) {
  const [url, setUrl] = useState(initialUrl ?? "");
  const [valid, setValid] = useState(true);

  useEffect(() => {
    setUrl(initialUrl ?? "");
  }, [initialUrl, open]);

  if (!open) return null;

  const handleConfirm = () => {
    try {
      if (url.trim().length === 0) return;
      // 简单校验 URL
      // eslint-disable-next-line no-new
      new URL(url);
      setValid(true);
      onConfirm(url.trim());
    } catch {
      setValid(false);
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.35)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
    }}>
      <div style={{ width: 520, maxWidth: "90%", background: "var(--color-bg, #fff)", borderRadius: 12, boxShadow: "0 10px 30px rgba(0,0,0,.2)", overflow: "hidden" }}>
        <div style={{ padding: 16, borderBottom: "1px solid var(--color-border,#e5e7eb)" }}>
          <strong>设置封面插图</strong>
        </div>
        <div style={{ padding: 16, display: "grid", gap: 12 }}>
          <label style={{ fontSize: 13, color: "var(--color-text-secondary,#6b7280)" }}>图片链接（支持 https://）</label>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="例如：https://example.com/cover.png"
            style={{
              width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid ${valid ? "var(--color-border,#e5e7eb)" : "#ef4444"}`,
              outline: "none"
            }}
          />
          {!valid && <span style={{ color: "#ef4444", fontSize: 12 }}>链接无效，请检查后重试。</span>}

          {url && (
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <img src={url} alt="预览" style={{ width: 160, height: 100, objectFit: "cover", borderRadius: 8, border: "1px solid var(--color-border,#e5e7eb)" }} />
              <div style={{ fontSize: 12, color: "var(--color-text-secondary,#6b7280)" }}>预览</div>
            </div>
          )}
        </div>
        <div style={{ padding: 16, borderTop: "1px solid var(--color-border,#e5e7eb)", display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button onClick={onClose} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid var(--color-border,#e5e7eb)", background: "transparent" }}>取消</button>
          <button onClick={handleConfirm} style={{ padding: "8px 12px", borderRadius: 8, border: "none", background: "var(--color-primary,#111827)", color: "#fff" }}>确定</button>
        </div>
      </div>
    </div>
  );
}
