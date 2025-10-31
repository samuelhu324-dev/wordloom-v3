"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { apiFetch } from '@/lib/api';

type Entry = {
  id: number | string;
  text?: string;
  translation?: string;
  source_name?: string;
  created_at?: string;
};

type Props = {
  limit?: number;              // 默认 10
  headTitle?: string;          // 标题
  linkTo?: "none" | "admin";   // 点击跳转
  showRefresh?: boolean;       // 是否显示刷新按钮
};

async function fetchLatestEntries(limit: number): Promise<Entry[]> {
  // 只传资源路径，由 apiFetch 拼接基址
  const url = `/entries?limit=${limit}&sort=created_at&order=desc&page=1`;
  const res = await apiFetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load latest entries: ${res.status}`);
  const data = await res.json();
  if (Array.isArray(data)) return data;
  if (Array.isArray((data as any)?.items)) return (data as any).items;
  if (Array.isArray((data as any)?.results)) return (data as any).results;
  return [];
}

function ItemSkeleton() {
  return (
    <li className="animate-pulse space-y-2 rounded-lg border p-4">
      <div className="h-4 w-3/4 bg-gray-200 rounded" />
      <div className="h-3 w-1/2 bg-gray-200 rounded" />
      <div className="h-3 w-24 bg-gray-200 rounded" />
    </li>
  );
}

export default function LatestList({
  limit = 10,
  headTitle = `最新 ${limit} 条`,
  linkTo = "admin",
  showRefresh = true,
}: Props) {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["latestEntries", limit],
    queryFn: () => fetchLatestEntries(limit),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const items = useMemo(() => data ?? [], [data]);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">{headTitle}</h2>
        {showRefresh && (
          <button
            onClick={() => refetch()}
            className="text-sm rounded-md border px-3 py-1 hover:bg-gray-50 disabled:opacity-60"
            disabled={isFetching}
            title="重新获取最新条目"
          >
            {isFetching ? "刷新中…" : "刷新"}
          </button>
        )}
      </div>

      {isError && (
        <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          加载失败：{(error as Error)?.message ?? "Unknown error"}
        </div>
      )}

      <ul className="space-y-3">
        {isLoading
          ? Array.from({ length: limit }).map((_, i) => <ItemSkeleton key={i} />)
          : items.map((it) => {
              const primary = it.text || it.translation || "(无内容)";
              const metaLeft = it.source_name ? `来源：${it.source_name}` : "来源：—";
              const metaRight = it.created_at
                ? new Date(it.created_at).toLocaleString()
                : "";

              const content = (
                <div className="rounded-lg border p-4 hover:bg-gray-50 transition">
                  <p className="text-[15px] leading-relaxed text-gray-800">{primary}</p>
                  <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                    <span>{metaLeft}</span>
                    <span>{metaRight}</span>
                  </div>
                </div>
              );

              return linkTo === "admin" ? (
                <li key={it.id}>
                  <Link href={`/admin?id=${encodeURIComponent(String(it.id))}`}>{content}</Link>
                </li>
              ) : (
                <li key={it.id}>{content}</li>
              );
            })}
      </ul>
    </div>
  );
}
