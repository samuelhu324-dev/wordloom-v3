"use client";
import { ReactNode } from "react";

export function EditDialog({
  open,
  onClose,
  children,
  title = "编辑条目"
}: {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
      <div className="w-full max-w-xl rounded-2xl bg-white p-4 shadow-xl">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button className="rounded border px-2 py-1" onClick={onClose}>×</button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
}
