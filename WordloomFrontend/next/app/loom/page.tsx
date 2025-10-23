"use client";
import "@/styles/wordloom-themes.css";
import { useMemo, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { APP } from "@/routes/tokens";
import { buildAppPath } from "@/routes/builders";
import InsertPanel from '@/modules/loom/ui/creation/InsertPanel';
import ManagePanel from '@/modules/loom/ui/management/ManagePanel';
import ThemeDock from '@/components/common/ThemeDock';

function TabLink({active, href, children}:{active:boolean; href:string; children:React.ReactNode}){
  return (
    <Link
      href={href}
      className={`px-3 py-2 border-b-2 ${active?"border-rose-500 text-rose-600":"border-transparent text-gray-600 hover:text-black"}`}
      aria-current={active ? "page" : undefined}
    >
      {children}
    </Link>
  );
}

export default function LoomPage(){
  const router = useRouter();
  const params = useSearchParams();
  const pathname = usePathname();

  const managementHref = useMemo(()=>buildAppPath(APP.LOOM_MANAGEMENT),[]);
  const creationHref   = useMemo(()=>buildAppPath(APP.LOOM_CREATION),[]);

  // 默认 /loom → Management
  useEffect(()=>{
    if (pathname === "/loom" && !params.get("tab")) {
      router.replace(managementHref);
    }
  }, [pathname, params, router, managementHref]);

  const tabParam = params.get("tab");
  const tab: "management"|"creation" = tabParam === "creation" ? "creation" : "management";

  return (
    <div className="loom-theme wl-pattern-surface">
      <h1 className="text-3xl font-semibold mb-3">Loom — Writing & Editing Hub</h1>

      <div className="sticky top-0 z-30 bg-white/80 backdrop-blur border-b">
        <div className="flex items-center gap-4">
          <TabLink active={tab==="management"} href={managementHref}>🛠 Management</TabLink>
          <TabLink active={tab==="creation"} href={creationHref}>📚 Creation</TabLink>
        </div>
      </div>

      <div className="py-4">
        {tab==="management" ? <ManagePanel/> : <InsertPanel/>}
      </div>

      <ThemeDock />
    </div>
  );
}
