"use client";

import { useEffect, useMemo, useState } from "react";
import ImageUrlDialog from "@/features/media/ui/ImageUrlDialog";
import { useI18n } from "@/i18n/useI18n";

type Props = {
  bookshelfId: string;
  title: string;
  description?: string | null;
};

const placeholder = "https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=1200&auto=format&fit=crop";

export default function BookshelfHeader({ bookshelfId, title, description }: Props) {
  const storageKey = useMemo(() => `bookshelf:cover:${bookshelfId}`, [bookshelfId]);
  const [open, setOpen] = useState(false);
  const [coverUrl, setCoverUrl] = useState<string | null>(null);
  const { t } = useI18n();

  useEffect(() => {
    try {
      const v = localStorage.getItem(storageKey);
      if (v) setCoverUrl(v);
    } catch {
      // ignore
    }
  }, [storageKey]);

  const onConfirm = (url: string) => {
    setCoverUrl(url);
    try { localStorage.setItem(storageKey, url); } catch {}
    setOpen(false);
  };

  return (
    <div style={{ position: "relative", borderRadius: 16, overflow: "hidden", background: "#0b0f16" }}>
      <div style={{ position: "relative", height: 220, background: "#111827" }}>
        <img
          src={coverUrl || placeholder}
          alt={t('bookshelves.header.coverAlt')}
          style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.95 }}
        />
        {/* Hover actions */}
        <div
          style={{ position: "absolute", top: 12, right: 12, display: "flex", gap: 8, opacity: 0, transition: "opacity .2s" }}
          className="wl-hover-actions"
        >
          <button
            title={t('bookshelves.header.coverAction')}
            onClick={() => setOpen(true)}
            style={{
              padding: 8,
              borderRadius: 10,
              background: "rgba(0,0,0,.55)",
              color: "#fff",
              border: "1px solid rgba(255,255,255,.2)",
              backdropFilter: "blur(6px)",
              cursor: "pointer"
            }}
          >🖼️</button>
        </div>
      </div>
      <style>{`
        .wl-hover-actions { pointer-events: none; }
        .wl-hover-actions button { pointer-events: auto; }
        .wl-cover-wrap:hover .wl-hover-actions { opacity: 1; }
      `}</style>
      <div style={{ position: "absolute", left: 16, bottom: 14, color: "#fff", textShadow: "0 2px 8px rgba(0,0,0,.45)" }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>{title}</h1>
        {description && <p style={{ margin: "6px 0 0 0", opacity: .92, maxWidth: 820 }}>{description}</p>}
      </div>

      {open && (
        <ImageUrlDialog
          open={open}
          initialUrl={coverUrl ?? undefined}
          onClose={() => setOpen(false)}
          onConfirm={onConfirm}
        />
      )}
    </div>
  );
}
