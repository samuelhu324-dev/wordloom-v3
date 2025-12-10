"use client";

import { useState, useMemo, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { listNotes, createNote, deleteNote, incrementNoteUsage, duplicateNote, listBookshelves, moveNoteToBookshelf, pinNote, unpinNote } from "@/modules/orbit/domain/api";
import { extractFirstImageFromHtml, extractFirstSentenceFromHtml } from "@/lib/imageUtils";
import type { Note } from "@/modules/orbit/domain/notes";
import type { Bookshelf } from "@/modules/orbit/domain/bookshelves";
import {
  Zap, Bug, TrendingUp, Clock, CheckCircle2,
  BookOpen, Link2, FileText, Code2, Lightbulb,
  AlertTriangle, Star, Smile, Pause, Flame,
  Palette, CheckCircle, Lock, Compass, Pin
} from "lucide-react";

type ViewMode = "grid" | "list";

const ICON_COMPONENTS: Record<string, any> = {
  Zap, Bug, TrendingUp, Clock, CheckCircle2,
  BookOpen, Link2, FileText, Code2, Lightbulb,
  AlertTriangle, Star, Smile, Pause, Flame,
  Palette, CheckCircle, Lock, Compass,
};

function renderIcon(name?: string | null, color: string = "#111827", size = 16) {
  if (!name) return null;
  const C = ICON_COMPONENTS[name];
  if (!C) return null;
  return <C size={size} color={color} strokeWidth={2} />;
}

function contrastColor(hex: string): string {
  const h = hex.replace('#','');
  const r = parseInt(h.substring(0,2),16);
  const g = parseInt(h.substring(2,4),16);
  const b = parseInt(h.substring(4,6),16);
  const brightness = (r*299+g*587+b*114)/1000;
  return brightness > 128 ? '#111827' : '#FFFFFF';
}

// 对标签进行字母排序的辅助函数
function getSortedTags(tags: any[] | undefined) {
  if (!tags || tags.length === 0) return [];
  return [...tags].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
}

export default function OrbitPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [searchQ, setSearchQ] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [tag, setTag] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState("-updated_at");
  const [priority, setPriority] = useState("");
  const [urgency, setUrgency] = useState("");
  const [usageCount, setUsageCount] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [showTagDropdown, setShowTagDropdown] = useState(false);
  const [duplicating, setDuplicating] = useState<string | null>(null);
  const [moving, setMoving] = useState<string | null>(null);
  const [moveNoteId, setMoveNoteId] = useState<string | null>(null);
  const [pinning, setPinning] = useState<string | null>(null);

  const { data: notes = [], isLoading, refetch } = useQuery({
    queryKey: ["orbit", "notes", { q: searchQ, tag, status, sort }],
    queryFn: () => listNotes({ q: searchQ, tag, status, sort, limit: 100, offset: 0 }),
    staleTime: 15_000,
  });

  const { data: bookshelves = [] } = useQuery({
    queryKey: ["orbit", "bookshelves"],
    queryFn: () => listBookshelves({ limit: 100, offset: 0 }),
    staleTime: 15_000,
  });

  // 页面可见性变化时自动刷新数据
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log("[NOTES] 页面变为可见，刷新数据");
        refetch();
      }
    };

    // 同时监听 focus 和 visibilitychange 事件
    window.addEventListener("focus", handleVisibilityChange);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("focus", handleVisibilityChange);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [refetch]);

  // 页面进入时刷新数据（确保显示最新的 Notes 数据）
  useEffect(() => {
    console.log("[NOTES] 页面进入/搜索条件变化，刷新数据");
    refetch();
  }, [searchQ, tag, status, sort, refetch]);

  const tags = useMemo(() => Array.from(new Set(notes.flatMap(n => n.tags))), [notes]);

  // 按字母排序标签，并根据输入过滤
  const sortedTags = useMemo(() => {
    const sorted = [...tags].sort();
    if (!tagInput) return sorted.slice(0, 10); // 没有输入时显示前 10 个
    return sorted.filter(t => t.toLowerCase().includes(tagInput.toLowerCase()));
  }, [tags, tagInput]);

  // 前端过滤逻辑
  const filteredNotes = useMemo(() => {
    const filtered = notes.filter(note => {
      if (priority && note.priority !== parseInt(priority)) return false;
      if (urgency && note.urgency !== parseInt(urgency)) return false;
      if (usageCount && note.usageCount !== parseInt(usageCount)) return false;
      return true;
    });

    // 分离pinned和unpinned，置顶的优先显示
    const pinned = filtered.filter(n => n.isPinned);
    const unpinned = filtered.filter(n => !n.isPinned);

    // 置顶的按pinnedAt降序排列
    pinned.sort((a, b) => {
      const dateA = a.pinnedAt ? new Date(a.pinnedAt).getTime() : 0;
      const dateB = b.pinnedAt ? new Date(b.pinnedAt).getTime() : 0;
      return dateB - dateA;
    });

    return [...pinned, ...unpinned];
  }, [notes, priority, urgency, usageCount]);

  const formatDate = (dateString: string | undefined | null) => {
    if (!dateString) return "未知时间";
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return "未知时间";
      return date.toLocaleString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "未知时间";
    }
  };

  async function onQuickCreate() {
    setCreating(true);
    try {
      const n = await createNote({ title: "Untitled", text: "" });
      await refetch();
      router.push(`/orbit/${n.id}`);
    } finally {
      setCreating(false);
    }
  }

  async function onDelete(noteId: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("确定删除这个 Note 吗？")) return;

    setDeleting(noteId);
    try {
      await deleteNote(noteId);
      await refetch();
    } finally {
      setDeleting(null);
    }
  }

  async function onDuplicate(noteId: string, e: React.MouseEvent) {
    e.stopPropagation();
    setDuplicating(noteId);
    try {
      const newNote = await duplicateNote(noteId);
      await refetch();
      alert(`已复制! 新 Note ID: ${newNote.id}`);
    } catch (err) {
      console.error("复制失败:", err);
      alert("复制失败，请重试");
    } finally {
      setDuplicating(null);
    }
  }

  async function onMoveToBookshelf(noteId: string, bookshelfId: string) {
    setMoving(bookshelfId);
    try {
      await moveNoteToBookshelf(noteId, bookshelfId);
      await refetch();
      setMoveNoteId(null);
      alert("Note 已移至书架！");
    } catch (err) {
      console.error("移动失败:", err);
      alert("移动失败，请重试");
    } finally {
      setMoving(null);
    }
  }

  async function onNoteClick(noteId: string) {
    try {
      await incrementNoteUsage(noteId);
      await refetch();
    } catch (e) {
      console.error("Failed to increment usage:", e);
    }
    router.push(`/orbit/${noteId}`);
  }

  async function onPin(noteId: string, e: React.MouseEvent) {
    e.stopPropagation();
    setPinning(noteId);
    try {
      await pinNote(noteId);
      await refetch();
    } catch (err) {
      console.error("[PIN] 置顶失败:", err);
    } finally {
      setPinning(null);
    }
  }

  async function onUnpin(noteId: string, e: React.MouseEvent) {
    e.stopPropagation();
    setPinning(noteId);
    try {
      await unpinNote(noteId);
      await refetch();
    } catch (err) {
      console.error("[UNPIN] 取消置顶失败:", err);
    } finally {
      setPinning(null);
    }
  }

  if (isLoading) return <main className="max-w-6xl mx-auto px-5 py-6">加载中…</main>;

  return (
    <main className="max-w-6xl mx-auto px-5 py-6">
      {/* 标题部分 */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2">Orbit • Notes</h1>
          <p className="text-gray-600">Quick Capture Hub</p>
        </div>
        <button
          onClick={() => router.push('/orbit/bookshelves')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          📚 My Bookshelves
        </button>
      </div>

      {/* 搜索和过滤 */}
      <div className="flex gap-4 mb-6 flex-wrap items-center justify-between">
        <div className="flex gap-4 flex-wrap items-center flex-1">
          <input
            type="text"
            placeholder="关键词 (Enter 搜索)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setSearchQ(q);
              }
            }}
            className="flex-1 min-w-48 rounded border p-2 text-sm"
          />
          <div className="relative">
            <input
              type="text"
              placeholder="标签 (Enter 选择)"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onFocus={() => setShowTagDropdown(true)}
              onBlur={() => setTimeout(() => setShowTagDropdown(false), 200)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && sortedTags.length > 0) {
                  setTag(sortedTags[0]);
                  setTagInput("");
                  setShowTagDropdown(false);
                }
              }}
              className="rounded border p-2 text-sm w-32"
            />
            {showTagDropdown && sortedTags.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded shadow-lg z-10 max-h-40 overflow-y-auto">
                {sortedTags.map(t => (
                  <div
                    key={t}
                    onClick={() => {
                      setTag(t);
                      setTagInput("");
                      setShowTagDropdown(false);
                    }}
                    className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm"
                  >
                    {t}
                  </div>
                ))}
              </div>
            )}
            {tag && (
              <div className="text-xs text-gray-500 mt-1">
                已选: <span className="font-semibold">{tag}</span>
                <button
                  onClick={() => setTag("")}
                  className="ml-2 text-red-500 hover:text-red-700"
                >
                  清除
                </button>
              </div>
            )}
          </div>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded border p-2 text-sm"
          >
            <option value="">全部状态</option>
            <option value="open">待办</option>
            <option value="done">完成</option>
          </select>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="rounded border p-2 text-sm"
          >
            <option value="">全部重要程度</option>
            {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>重要程度 {n}</option>)}
          </select>
          <select
            value={urgency}
            onChange={(e) => setUrgency(e.target.value)}
            className="rounded border p-2 text-sm"
          >
            <option value="">全部紧急程度</option>
            {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>紧急程度 {n}</option>)}
          </select>
          <select
            value={usageCount}
            onChange={(e) => setUsageCount(e.target.value)}
            className="rounded border p-2 text-sm"
          >
            <option value="">按使用次数</option>
            <option value="0">未使用 (0)</option>
            <option value="1">已使用 (1+)</option>
          </select>
        </div>

        {/* 视图切换 + 新建按钮 */}
        <div className="flex gap-2 items-center">
          <div className="flex gap-1 border rounded p-1 bg-gray-100">
            <button
              onClick={() => setViewMode("grid")}
              title="卡片视图"
              className={`px-3 py-1 rounded text-sm transition ${
                viewMode === "grid"
                  ? "bg-white text-blue-600 shadow"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h18M3 12h18M3 21h18M9 3v18M15 3v18" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode("list")}
              title="列表视图"
              className={`px-3 py-1 rounded text-sm transition ${
                viewMode === "list"
                  ? "bg-white text-blue-600 shadow"
                  : "text-gray-600 hover:text-gray-800"
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7h18M3 12h18M3 17h18" />
              </svg>
            </button>
          </div>
          <button
            onClick={onQuickCreate}
            disabled={creating}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {creating ? "创建中…" : "新建 Note"}
          </button>
        </div>
      </div>

      {/* 笔记列表 */}
      {filteredNotes.length === 0 ? (
        <div className="text-center py-12 text-gray-500">暂无 Note</div>
      ) : viewMode === "grid" ? (
        /* 卡片视图 */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredNotes.map(note => {
            const firstImage = extractFirstImageFromHtml(note.text);
            return (
              <div
                key={note.id}
                onClick={() => onNoteClick(note.id)}
                className="relative group p-4 border rounded hover:shadow-md hover:cursor-pointer transition"
              >
                {/* 置顶徽章 */}
                {note.isPinned && (
                  <div className="absolute top-2 left-2 bg-red-500 text-white p-1 rounded z-20">
                    <Pin size={14} fill="currentColor" />
                  </div>
                )}
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition flex gap-1">
                  <button
                    onClick={(e) =>
                      note.isPinned ? onUnpin(note.id, e) : onPin(note.id, e)
                    }
                    disabled={pinning === note.id}
                    className="p-1 bg-amber-500 hover:bg-amber-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs disabled:opacity-50"
                    title={note.isPinned ? "取消置顶" : "置顶"}
                  >
                    <Pin size={14} fill={note.isPinned ? "currentColor" : "none"} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setMoveNoteId(note.id);
                    }}
                    className="p-1 bg-green-500 hover:bg-green-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                    title="移动到书架"
                  >
                    📚
                  </button>
                  <button
                    onClick={(e) => onDuplicate(note.id, e)}
                    disabled={duplicating === note.id}
                    className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs disabled:opacity-50"
                    title="复制"
                  >
                    {duplicating === note.id ? "…" : "📋"}
                  </button>
                  <button
                    onClick={(e) => onDelete(note.id, e)}
                    disabled={deleting === note.id}
                    className="p-1 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm disabled:opacity-50"
                    title="删除"
                  >
                    {deleting === note.id ? "…" : "×"}
                  </button>
                </div>

                {/* 移动到书架模态 */}
                {moveNoteId === note.id && (
                  <div className="absolute top-12 right-2 bg-white border rounded shadow-lg p-3 z-10 w-40">
                    <p className="text-xs font-semibold mb-2">移动到书架：</p>
                    {bookshelves.length === 0 ? (
                      <p className="text-xs text-gray-500">暂无书架</p>
                    ) : (
                      <div className="flex flex-col gap-1">
                        {bookshelves.map(bs => (
                          <button
                            key={bs.id}
                            onClick={(e) => {
                              e.stopPropagation();
                              onMoveToBookshelf(note.id, bs.id);
                            }}
                            disabled={moving === bs.id}
                            className="text-left px-2 py-1 text-xs hover:bg-gray-100 rounded disabled:opacity-50"
                          >
                            {moving === bs.id ? "移动中…" : bs.name}
                          </button>
                        ))}
                      </div>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setMoveNoteId(null);
                      }}
                      className="text-xs text-gray-500 mt-2"
                    >
                      取消
                    </button>
                  </div>
                )}

                {firstImage && (
                  <img
                    src={firstImage}
                    alt="preview"
                    className="w-full h-32 object-cover rounded mb-3"
                    onError={(e) => {
                      console.error("图片加载失败:", firstImage);
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                )}

                <h3 className="font-semibold text-sm mb-2">{note.title || "Untitled"}</h3>

                {note.text && (
                  <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                    {extractFirstSentenceFromHtml(note.text)}
                  </p>
                )}

                <div className="flex gap-2 mb-2 text-xs text-gray-500">
                  <span>优先级: {note.priority}</span>
                  <span>紧急: {note.urgency}</span>
                  <span>使用: {note.usageCount || 0}</span>
                </div>

                <p className="text-xs text-gray-500 mb-2">
                  {formatDate(note.updatedAt || note.createdAt)}
                </p>

                {note.tagsRel && note.tagsRel.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {getSortedTags(note.tagsRel).map(t => (
                      <div
                        key={t.id}
                        className="inline-flex items-center gap-1 px-2 py-1 text-white rounded text-xs font-medium"
                        style={{ backgroundColor: t.color }}
                      >
                        <span className="inline-flex items-center gap-1">
                          {renderIcon(t.icon, "#FFFFFF", 14)}
                          {t.name}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* 列表视图 */
        <div className="divide-y divide-gray-200">
          {filteredNotes.map(note => {
            const firstImage = extractFirstImageFromHtml(note.text);
            return (
              <div
                key={note.id}
                onClick={() => onNoteClick(note.id)}
                className="flex gap-4 p-4 hover:shadow-md transition cursor-pointer relative group items-start"
              >
                {/* 置顶徽章 */}
                {note.isPinned && (
                  <div className="absolute top-4 left-4 bg-red-500 text-white p-1 rounded z-20">
                    <Pin size={14} fill="currentColor" />
                  </div>
                )}
                {/* 左侧图片缩略图 */}
                {firstImage && (
                  <div className="flex-shrink-0 w-24 h-24 bg-gray-200 rounded overflow-hidden">
                    <img
                      src={firstImage}
                      alt="preview"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                      }}
                    />
                  </div>
                )}

                {/* 删除按钮（X 图标） */}
                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition flex gap-1">
                  <button
                    onClick={(e) =>
                      note.isPinned ? onUnpin(note.id, e) : onPin(note.id, e)
                    }
                    disabled={pinning === note.id}
                    className="p-1 bg-amber-500 hover:bg-amber-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm disabled:opacity-50"
                    title={note.isPinned ? "取消置顶" : "置顶"}
                  >
                    <Pin size={16} fill={note.isPinned ? "currentColor" : "none"} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setMoveNoteId(note.id);
                    }}
                    className="p-1 bg-green-500 hover:bg-green-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm"
                    title="移动到书架"
                  >
                    📚
                  </button>
                  <button
                    onClick={(e) => onDuplicate(note.id, e)}
                    disabled={duplicating === note.id}
                    className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm disabled:opacity-50"
                    title="复制"
                  >
                    {duplicating === note.id ? "…" : "📋"}
                  </button>
                  <button
                    onClick={(e) => onDelete(note.id, e)}
                    disabled={deleting === note.id}
                    className="p-1 bg-red-500 hover:bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm disabled:opacity-50"
                    title="删除"
                  >
                    {deleting === note.id ? "…" : "×"}
                  </button>
                </div>

                {/* 移动到书架模态 */}
                {moveNoteId === note.id && (
                  <div className="absolute top-12 right-4 bg-white border rounded shadow-lg p-3 z-10 w-40">
                    <p className="text-xs font-semibold mb-2">移动到书架：</p>
                    {bookshelves.length === 0 ? (
                      <p className="text-xs text-gray-500">暂无书架</p>
                    ) : (
                      <div className="flex flex-col gap-1">
                        {bookshelves.map(bs => (
                          <button
                            key={bs.id}
                            onClick={(e) => {
                              e.stopPropagation();
                              onMoveToBookshelf(note.id, bs.id);
                            }}
                            disabled={moving === bs.id}
                            className="text-left px-2 py-1 text-xs hover:bg-gray-100 rounded disabled:opacity-50"
                          >
                            {moving === bs.id ? "移动中…" : bs.name}
                          </button>
                        ))}
                      </div>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setMoveNoteId(null);
                      }}
                      className="text-xs text-gray-500 mt-2"
                    >
                      取消
                    </button>
                  </div>
                )}

                <div className="flex-1">
                  <h3 className="font-semibold text-base mb-1">{note.title || "Untitled"}</h3>

                  {note.text && (
                    <p className="text-sm text-gray-600 mb-2">
                      {extractFirstSentenceFromHtml(note.text)}
                    </p>
                  )}

                  <div className="flex gap-3 mb-2 text-xs text-gray-500">
                    <span>优先级: {note.priority}</span>
                    <span>紧急: {note.urgency}</span>
                    <span>使用: {note.usageCount || 0}</span>
                    <span>{formatDate(note.updatedAt || note.createdAt)}</span>
                  </div>

                  {note.tagsRel && note.tagsRel.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {getSortedTags(note.tagsRel).map(t => (
                        <div
                          key={t.id}
                          className="inline-flex items-center gap-1 px-3 py-1 text-white rounded text-xs font-medium"
                          style={{ backgroundColor: t.color }}
                        >
                          <span className="inline-flex items-center gap-1">
                            {renderIcon(t.icon, "#FFFFFF", 14)}
                            {t.name}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}
