"use client"

import { useMemo, useEffect, useState } from "react"
import Link from "next/link"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { APP } from "@/routes/tokens"
import { buildAppPath } from "@/routes/builders"
import InsertPanel from '@/modules/loom/ui/creation/InsertPanel'
import ManagePanel from '@/modules/loom/ui/management/ManagePanel'
import ThemeDock from '@/components/common/ThemeDock'
import * as Lucide from "lucide-react"
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

function TabLink({active, href, children}:{active:boolean; href:string; children:React.ReactNode}){
  return (
    <Link
      href={href}
      className={`px-3 py-2 border-b-2 ${active?"tab-active":"tab-inactive"}`}
      aria-current={active ? "page" : undefined}
    >
      {children}
    </Link>
  )
}

type Document = {
  id: number
  title: string
  content: string
  tags: string[]
  updated: string
  words: number
  favorite?: boolean
}

export default function LoomPage(){
  const router = useRouter()
  const params = useSearchParams()
  const pathname = usePathname()

  const managementHref = useMemo(()=>buildAppPath(APP.LOOM_MANAGEMENT),[])
  const creationHref   = useMemo(()=>buildAppPath(APP.LOOM_CREATION),[])

  // 默认 /loom → Management
  useEffect(()=>{
    if (pathname === "/loom" && !params.get("tab")) {
      router.replace(managementHref)
    }
  }, [pathname, params, router, managementHref])

  const tabParam = params.get("tab")
  const tab = tabParam ?? "management"

  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTag, setSelectedTag] = useState<string>('')
  
  // 模拟数据
  const [documents] = useState<Document[]>([
    { 
      id: 1, 
      title: "Project Proposal", 
      content: "A comprehensive project proposal for Q4...",
      tags: ["work", "proposal"],
      updated: "2 hours ago", 
      words: 1234,
      favorite: true
    },
    { 
      id: 2, 
      title: "Meeting Notes", 
      content: "Notes from the weekly team meeting...",
      tags: ["meeting", "notes"],
      updated: "1 day ago", 
      words: 567
    },
    { 
      id: 3, 
      title: "Blog Draft", 
      content: "Draft for the upcoming blog post about...",
      tags: ["blog", "draft"],
      updated: "3 days ago", 
      words: 2891,
      favorite: true
    },
    { 
      id: 4, 
      title: "Research Notes", 
      content: "Research findings and references...",
      tags: ["research"],
      updated: "1 week ago", 
      words: 1456
    },
  ])

  const allTags = Array.from(new Set(documents.flatMap(d => d.tags)))
  const stats = {
    total: documents.length,
    words: documents.reduce((sum, d) => sum + d.words, 0),
    favorites: documents.filter(d => d.favorite).length
  }

  return (
    <main className={`relative loom-skin loom-skin-business loom-weave-bg min-h-svh`}>
     {/* Orbit 风格标题：左侧渐变图标 + 主副标题 + 下方分隔线 */}
     <header className="px-4 sm:px-6 pt-5">
       <div className="flex items-center gap-5">
         <div
           className="h-16 w-16 sm:h-18 sm:w-18 rounded-2xl text-white flex items-center justify-center
                      bg-gradient-to-br from-[hsl(var(--loom-from))] to-[hsl(var(--loom-to))]
                      shadow-[0_10px_30px_-12px_hsl(var(--loom-from)/.55)]
                      ring-1 ring-white/20"
         >
           <Lucide.PenLine className="h-8 w-8 sm:h-9 sm:w-9" />
         </div>

         <div className="min-w-0">
           <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">Loom Hub</h1>
           <p className="text-base sm:text-lg text-muted-foreground">Writing & Editing Hub</p>
         </div>
       </div>

       {/* 更粗的分隔线 */}
       <div className="mt-4 border-b-2 border-border/70" />
     </header>

      {/* 你的 Tab 区域，图标换成 Lucide 样式 */}
      <div className="px-4 sm:px-6 pt-3">
        <div className="flex items-center gap-3">
          <a
            href={managementHref}
            className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm sm:text-base transition
              ${tab==="management"
                ? "bg-white/75 dark:bg-white/10 text-foreground shadow"
                : "text-muted-foreground hover:bg-white/50 dark:hover:bg-white/5"}`}
          >
            <Lucide.Scissors className="h-5 w-5" />
            Management
          </a>
          <a
            href={creationHref}
            className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm sm:text-base transition
              ${tab==="creation"
                ? "bg-white/75 dark:bg-white/10 text-foreground shadow"
                : "text-muted-foreground hover:bg-white/50 dark:hover:bg-white/5"}`}
          >
            <Lucide.PenLine className="h-5 w-5" />
            Creation
          </a>
        </div>
      </div>

      {/* 下面保持你的原有内容区 */}
      <div className="py-4">
        {tab==="management" ? <ManagePanel/> : <InsertPanel/>}
      </div>

      <ThemeDock />
    </main>
  )
}
