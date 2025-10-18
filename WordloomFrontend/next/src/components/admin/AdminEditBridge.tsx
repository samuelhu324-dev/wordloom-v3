"use client";

import dynamic from "next/dynamic";
import React from "react";

type Entry = {
  id: number | string;
  text?: string;
  translation?: string;
  source_name?: string;
  created_at?: string;
};

type Props = {
  entryId?: string;
  entry?: Entry | null;
  autoOpen?: boolean;              // 进入页面即自动打开
  onSaved?: (e?: Entry | null) => void;
};

// 动态加载，禁用 SSR，避免服务端期望 UI 事件
const EditDialog = dynamic(
  async () => {
    const mod = await import("@/components/common/EditDialog");
    // 兼容三种情况：default / EditDialog / EntryDialog
    return (mod as any).default ?? (mod as any).EditDialog ?? (mod as any).EntryDialog;
  },
  {
    ssr: false,
    loading: () => (
      <div className="text-xs text-gray-500">正在加载编辑器组件…</div>
    ),
  }
);


export default function AdminEditBridge({
  entryId,
  entry,
  autoOpen = false,
  onSaved,
}: Props) {
  const [open, setOpen] = React.useState<boolean>(!!autoOpen);

  // 当 entryId 改变时，若启用 autoOpen，则重新打开一次
  React.useEffect(() => {
    if (autoOpen) setOpen(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entryId]);

  const handleSaved = React.useCallback(() => {
    onSaved?.(entry ?? null);
    setOpen(false);
  }, [onSaved, entry]);

  return (
    <div>
      {/* 主编辑对话框：同时传入 entry 与 entryId，最大化兼容 */}
      {/* 大多数情况下 EditDialog 接收 open/onOpenChange 或 open/onClose，其它会被忽略 */}
      {/* @ts-ignore - 允许宽松传参以适配未知的 prop 形状 */}
      <EditDialog
        open={open}
        onOpenChange={setOpen}
        onClose={() => setOpen(false)}
        entry={entry ?? undefined}
        entryId={entryId ?? undefined}
        onSaved={handleSaved}
      />

      {/* 兜底：若用户手动关闭了弹窗，这个按钮用于再次打开 */}
      <div className="mt-3">
        <button
          className="rounded-md border px-3 py-1 text-sm hover:bg-gray-50"
          onClick={() => setOpen(true)}
          disabled={!entryId && !entry}
          title="再次打开编辑对话框"
        >
          打开编辑对话框
        </button>
      </div>
    </div>
  );
}
