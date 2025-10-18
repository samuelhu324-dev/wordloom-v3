"use client";
import React from "react";

type Props = {
  page: number;           // 1-based
  pageSize: number;
  total: number;
  onChange: (nextPage: number) => void;
};

export default function Pagination({ page, pageSize, total, onChange }: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);

  const canPrev = safePage > 1;
  const canNext = safePage < totalPages;

  return (
    <div className="mt-4 flex items-center justify-between">
      <div className="text-sm text-gray-500">
        第 <span className="font-medium">{safePage}</span> / {totalPages} 页
        <span className="ml-2">（共 {total} 条）</span>
      </div>
      <div className="space-x-2">
        <button
          className="rounded-md border px-3 py-1 text-sm disabled:opacity-50"
          disabled={!canPrev}
          onClick={() => onChange(safePage - 1)}
        >
          上一页
        </button>
        <button
          className="rounded-md border px-3 py-1 text-sm disabled:opacity-50"
          disabled={!canNext}
          onClick={() => onChange(safePage + 1)}
        >
          下一页
        </button>
      </div>
    </div>
  );
}
