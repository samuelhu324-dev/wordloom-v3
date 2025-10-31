/**
 * Bookshelf 详情页 (/orbit/bookshelves/[id])
 * 显示 Bookshelf 内的所有 Notes，支持查看、添加、移除 Notes
 */

"use client";

import { useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useBookshelf, useBookshelfNotes, useRemoveNoteFromBookshelf, useIncrementBookshelfUsage } from "@/hooks/useBookshelf";
import { listNotes, incrementNoteUsage } from "@/modules/orbit/domain/api";
import { useQuery } from "@tanstack/react-query";
import type { Note } from "@/modules/orbit/domain/notes";
import {
  ArrowLeft, Search, Grid3x3, List, Trash2, MoreVertical, Plus,
  BookOpen, Clock, Zap, FileText, AlertCircle
} from "lucide-react";

type ViewMode = "grid" | "list";

export default function BookshelfDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookshelfId = params.id as string;

  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQ, setSearchQ] = useState("");
  const [sortBy, setSortBy] = useState("-updated_at");
  const [showAddModal, setShowAddModal] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);

  // 获取 Bookshelf 详情
  const { data: bookshelf, isLoading: bsLoading } = useBookshelf(bookshelfId);

  // 获取 Bookshelf 内的 Notes
  const { data: notesInShelf = [], isLoading: notesLoading } = useBookshelfNotes(bookshelfId, {
    sortBy: sortBy as any,
  });

  // 获取所有 Notes（用于添加）
  const { data: allNotes = [] } = useQuery({
    queryKey: ["orbit", "all-notes"],
    queryFn: () => listNotes({ limit: 1000 }),
  });

  const removeMutation = useRemoveNoteFromBookshelf();
  const incrementMutation = useIncrementBookshelfUsage();

  // 过滤搜索
  const filteredNotes = useMemo(() => {
    return notesInShelf.filter((n) =>
      n.title?.toLowerCase().includes(searchQ.toLowerCase()) ||
      n.text?.toLowerCase().includes(searchQ.toLowerCase())
    );
  }, [notesInShelf, searchQ]);

  // 可用的 Notes（不在此 Bookshelf 中）
  const availableNotes = useMemo(() => {
    return allNotes.filter(
      (n) => !notesInShelf.some((ns) => ns.id === n.id) && !n.bookshelfId
    );
  }, [allNotes, notesInShelf]);

  const handleRemoveNote = async (noteId: string) => {
    if (!confirm("确定要从此书架中移除该 Note？")) return;

    try {
      await removeMutation.mutateAsync({ bookshelfId, noteId });
      setRemoving(null);
    } catch (error) {
      console.error("移除失败:", error);
    }
  };

  const handleUseBookshelf = async () => {
    try {
      await incrementMutation.mutateAsync(bookshelfId);
    } catch (error) {
      console.error("更新使用次数失败:", error);
    }
  };

  const handleNoteClick = (noteId: string) => {
    handleUseBookshelf();
    router.push(`/orbit/${noteId}`);
  };

  if (bsLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!bookshelf) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <AlertCircle size={48} className="text-red-500 mb-4" />
        <p className="text-slate-600 text-lg mb-4">找不到此书架</p>
        <button
          onClick={() => router.push("/orbit/bookshelves")}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          返回书架列表
        </button>
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-gradient-to-br from-slate-50 to-slate-100 p-6 overflow-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.push("/orbit/bookshelves")}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4 transition"
        >
          <ArrowLeft size={20} />
          返回书架列表
        </button>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-6"
          style={{ borderLeftWidth: "8px", borderLeftColor: bookshelf.color || "#3b82f6" }}>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-4xl font-bold text-slate-900 mb-2">{bookshelf.name}</h1>
              {bookshelf.description && (
                <p className="text-slate-600 text-lg mb-4">{bookshelf.description}</p>
              )}
              <div className="flex gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <FileText size={16} className="text-slate-400" />
                  <span className="text-slate-600">{bookshelf.noteCount} Notes</span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap size={16} className="text-slate-400" />
                  <span className="text-slate-600">{bookshelf.usageCount} 次使用</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={16} className="text-slate-400" />
                  <span className="text-slate-600">
                    创建于 {new Date(bookshelf.createdAt || "").toLocaleDateString("zh-CN")}
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
            >
              <Plus size={20} />
              添加 Note
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex gap-3 flex-wrap">
          {/* 搜索框 */}
          <div className="flex-1 min-w-[250px] relative">
            <Search size={18} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="搜索 Notes..."
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            />
          </div>

          {/* 排序 */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg bg-white hover:bg-slate-50 transition"
          >
            <option value="-updated_at">最近更新</option>
            <option value="-created_at">最新创建</option>
            <option value="created_at">最早创建</option>
          </select>

          {/* 视图切换 */}
          <div className="flex gap-2 border border-slate-300 rounded-lg p-1 bg-white">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-2 rounded ${
                viewMode === "grid"
                  ? "bg-blue-500 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Grid3x3 size={18} />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-2 rounded ${
                viewMode === "list"
                  ? "bg-blue-500 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <List size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* 添加 Note 对话框 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold mb-6">添加 Note</h2>
            {availableNotes.length === 0 ? (
              <p className="text-slate-600 text-center py-8">没有可用的 Notes</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {availableNotes.map((note) => (
                  <button
                    key={note.id}
                    onClick={() => {
                      // TODO: 添加 Note 到 Bookshelf
                      setShowAddModal(false);
                    }}
                    className="w-full text-left p-3 border border-slate-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition"
                  >
                    <div className="font-medium text-slate-900">{note.title || "无标题"}</div>
                    <div className="text-sm text-slate-600 line-clamp-1">{note.text}</div>
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notes 内容区域 */}
      {notesLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-slate-600">加载中...</p>
          </div>
        </div>
      ) : filteredNotes.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-96 text-center">
          <BookOpen size={48} className="text-slate-300 mb-4" />
          <p className="text-slate-600 text-lg mb-4">此书架中没有 Notes</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            添加 Note
          </button>
        </div>
      ) : viewMode === "grid" ? (
        // 网格视图
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredNotes.map((note) => (
            <div
              key={note.id}
              onClick={() => handleNoteClick(note.id)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer p-6 group"
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold text-slate-900 flex-1 line-clamp-2">
                  {note.title || "无标题"}
                </h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemoveNote(note.id);
                  }}
                  className="p-1 text-slate-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition"
                  title="从书架中移除"
                >
                  <Trash2 size={18} />
                </button>
              </div>
              <p className="text-sm text-slate-600 line-clamp-3 mb-4">{note.text}</p>
              <div className="flex gap-2 text-xs text-slate-500">
                <span>优先级: {note.priority || 3}</span>
                <span>紧急: {note.urgency || 3}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        // 列表视图
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">标题</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">内容预览</th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900">优先级</th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900">操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredNotes.map((note) => (
                <tr
                  key={note.id}
                  onClick={() => handleNoteClick(note.id)}
                  className="border-b border-slate-200 hover:bg-slate-50 cursor-pointer transition"
                >
                  <td className="px-6 py-4 font-medium text-slate-900">
                    {note.title || "无标题"}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600 max-w-xs truncate">
                    {note.text}
                  </td>
                  <td className="px-6 py-4 text-center text-sm">
                    <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 rounded">
                      {note.priority || 3}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveNote(note.id);
                      }}
                      className="p-1 text-slate-400 hover:text-red-600 transition"
                      title="从书架中移除"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
