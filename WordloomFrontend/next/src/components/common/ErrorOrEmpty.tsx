"use client";

import React from "react";

type Props = {
  error?: string | null;
  empty?: boolean;
  retry?: () => void;
  className?: string;
};

/**
 * 标准错误/空态卡片组件
 * - error 优先显示；否则当 empty=true 时显示空态
 */
export default function ErrorOrEmpty({ error, empty, retry, className }: Props) {
  if (error) {
    return (
      <div className={`rounded-xl border p-6 ${className || ""}`} style={{ background: "var(--surface)", borderColor: "var(--ring)" }}>
        <div className="text-base font-semibold" style={{ color: "var(--accent)" }}>出错啦</div>
        <p className="mt-2 text-sm" style={{ color: "var(--muted)" }}>{error}</p>
        {retry && <button onClick={retry} className="mt-3 h-8 px-3 rounded border text-sm">重试</button>}
      </div>
    );
  }
  if (empty) {
    return (
      <div className={`rounded-xl border p-6 ${className || ""}`} style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <div className="text-base font-semibold">暂无数据</div>
        <p className="mt-2 text-sm" style={{ color: "var(--muted)" }}>可以调整筛选条件或尝试新增内容。</p>
      </div>
    );
  }
  return null;
}
