/**
 * Bookshelves 列表页 (/orbit/bookshelves)
 * 显示所有 Bookshelf 分类，支持网格视图、列表视图、搜索、排序等功能
 */

"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useBookshelves, useCreateBookshelf, useDeleteBookshelf, useUpdateBookshelf } from "@/hooks/useBookshelf";
import type { Bookshelf, BookshelfCreateRequest } from "@/modules/orbit/domain/bookshelves";
import {
  Plus, Search, Grid3x3, List, Star, MoreVertical, Edit2, Trash2,
  Archive, FolderOpen, Clock, BookOpen
} from "lucide-react";

type ViewMode = "grid" | "list";

export default function BookshelvesPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQ, setSearchQ] = useState("");
  const [status, setStatus] = useState<"active" | "archived" | "all">("active");
  const [sortBy, setSortBy] = useState("-created_at");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [showMenu, setShowMenu] = useState<string | null>(null);

  // 新建表单
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newIcon, setNewIcon] = useState("");
  const [newColor, setNewColor] = useState("#3b82f6");

  const { data: bookshelves = [], isLoading } = useBookshelves({
    status,
    sortBy: sortBy as any,
  });

  const createMutation = useCreateBookshelf();
  const updateMutation = useUpdateBookshelf();
  const deleteMutation = useDeleteBookshelf();

  // 过滤搜索
  const filtered = useMemo(() => {
    return bookshelves.filter((b) =>
      b.name.toLowerCase().includes(searchQ.toLowerCase()) ||
      b.description?.toLowerCase().includes(searchQ.toLowerCase())
    );
  }, [bookshelves, searchQ]);

  const handleCreate = async () => {
    if (!newName.trim()) return;

    try {
      await createMutation.mutateAsync({
        name: newName,
        description: newDescription,
        icon: newIcon,
        color: newColor,
      } as BookshelfCreateRequest);

      setNewName("");
      setNewDescription("");
      setNewIcon("");
      setNewColor("#3b82f6");
      setCreating(false);
    } catch (error) {
      console.error("创建失败:", error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除此 Bookshelf？其中的 Notes 将变为自由 Notes。")) return;

    try {
      await deleteMutation.mutateAsync({ id, cascade: "orphan" });
      setDeleting(null);
    } catch (error) {
      console.error("删除失败:", error);
    }
  };

  const handleRowClick = (id: string) => {
    router.push(`/orbit/bookshelves/${id}`);
  };

  return (
    <div className="h-screen w-full bg-gradient-to-br from-slate-50 to-slate-100 p-6 overflow-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 mb-2">📚 我的书架</h1>
            <p className="text-slate-600">整理和管理你的 Notes</p>
          </div>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            <Plus size={20} />
            新建书架
          </button>
        </div>

        {/* Controls */}
        <div className="flex gap-3 flex-wrap">
          {/* 搜索框 */}
          <div className="flex-1 min-w-[250px] relative">
            <Search size={18} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="搜索书架..."
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            />
          </div>

          {/* 状态过滤 */}
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as any)}
            className="px-4 py-2 border border-slate-300 rounded-lg bg-white hover:bg-slate-50 transition"
          >
            <option value="active">活跃</option>
            <option value="archived">已归档</option>
            <option value="all">全部</option>
          </select>

          {/* 排序 */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg bg-white hover:bg-slate-50 transition"
          >
            <option value="-created_at">最新创建</option>
            <option value="created_at">最早创建</option>
            <option value="name">名称 A-Z</option>
            <option value="-name">名称 Z-A</option>
            <option value="-note_count">Notes 最多</option>
            <option value="note_count">Notes 最少</option>
            <option value="-updated_at">最近更新</option>
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

      {/* 创建对话框 */}
      {creating && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold mb-6">创建新书架</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="书架名称（必填）"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <textarea
                placeholder="描述（可选）"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
              <input
                type="text"
                placeholder="图标名称（如：BookOpen, FolderOpen）"
                value={newIcon}
                onChange={(e) => setNewIcon(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-slate-700">颜色：</label>
                <input
                  type="color"
                  value={newColor}
                  onChange={(e) => setNewColor(e.target.value)}
                  className="w-16 h-10 rounded cursor-pointer"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setCreating(false);
                  setNewName("");
                  setNewDescription("");
                  setNewIcon("");
                  setNewColor("#3b82f6");
                }}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition"
              >
                取消
              </button>
              <button
                onClick={handleCreate}
                disabled={!newName.trim() || createMutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {createMutation.isPending ? "创建中..." : "创建"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 内容区域 */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-slate-600">加载中...</p>
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-96 text-center">
          <BookOpen size={48} className="text-slate-300 mb-4" />
          <p className="text-slate-600 text-lg mb-4">没有找到书架</p>
          <button
            onClick={() => setCreating(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            创建第一个书架
          </button>
        </div>
      ) : viewMode === "grid" ? (
        // 网格视图
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((bs) => (
            <div
              key={bs.id}
              onClick={() => handleRowClick(bs.id)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer overflow-hidden group"
              style={{
                borderTop: `4px solid ${bs.color || "#3b82f6"}`,
              }}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-slate-900 mb-1">{bs.name}</h3>
                    {bs.description && (
                      <p className="text-sm text-slate-600 line-clamp-2">{bs.description}</p>
                    )}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenu(showMenu === bs.id ? null : bs.id);
                    }}
                    className="p-1 text-slate-400 hover:text-slate-600"
                  >
                    <MoreVertical size={18} />
                  </button>
                </div>

                {/* 统计 */}
                <div className="flex gap-4 text-sm text-slate-600 mb-4">
                  <div className="flex items-center gap-1">
                    <FileText size={16} />
                    <span>{bs.noteCount} Notes</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Zap size={16} />
                    <span>{bs.usageCount} 次</span>
                  </div>
                </div>

                {/* 菜单 */}
                {showMenu === bs.id && (
                  <div className="absolute bg-white border border-slate-200 rounded-lg shadow-lg z-10">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // TODO: 编辑功能
                      }}
                      className="block w-full text-left px-4 py-2 hover:bg-slate-50"
                    >
                      <Edit2 size={16} className="inline mr-2" />
                      编辑
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(bs.id);
                      }}
                      className="block w-full text-left px-4 py-2 hover:bg-red-50 text-red-600"
                    >
                      <Trash2 size={16} className="inline mr-2" />
                      删除
                    </button>
                  </div>
                )}
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
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">名称</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">描述</th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900">Notes</th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900">使用次数</th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-slate-900">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((bs) => (
                <tr
                  key={bs.id}
                  onClick={() => handleRowClick(bs.id)}
                  className="border-b border-slate-200 hover:bg-slate-50 cursor-pointer transition"
                >
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-900">{bs.name}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600 max-w-xs truncate">
                    {bs.description || "-"}
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-slate-600">{bs.noteCount}</td>
                  <td className="px-6 py-4 text-center text-sm text-slate-600">{bs.usageCount}</td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowMenu(showMenu === bs.id ? null : bs.id);
                      }}
                      className="p-1 text-slate-400 hover:text-slate-600"
                    >
                      <MoreVertical size={18} />
                    </button>
                    {showMenu === bs.id && (
                      <div className="absolute bg-white border border-slate-200 rounded-lg shadow-lg z-10">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            // TODO: 编辑功能
                          }}
                          className="block w-full text-left px-4 py-2 hover:bg-slate-50"
                        >
                          <Edit2 size={16} className="inline mr-2" />
                          编辑
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(bs.id);
                          }}
                          className="block w-full text-left px-4 py-2 hover:bg-red-50 text-red-600"
                        >
                          <Trash2 size={16} className="inline mr-2" />
                          删除
                        </button>
                      </div>
                    )}
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

// 导入使用的 icon
import { FileText, Zap } from "lucide-react";
