"use client";
import { useEffect } from "react";
import Link from "next/link";
import { APP } from "@/routes/tokens";
import { buildAppPath } from "@/routes/builders";

export default function InsertRedirectPage(){
  const target = buildAppPath(APP.LOOM_CREATION);
  useEffect(()=>{ if (typeof window !== "undefined") { window.location.replace(target); } }, [target]);
  return (
    <div className="max-w-xl py-12">
      <h1 className="text-2xl font-semibold">页面迁移中</h1>
      <p className="mt-3 text-gray-600">Insert 已合并至 <strong>Loom → Creation</strong> 面板。</p>
      <p className="mt-2"><Link href={target} className="text-blue-600 underline">立即前往新的入口</Link></p>
    </div>
  );
}
