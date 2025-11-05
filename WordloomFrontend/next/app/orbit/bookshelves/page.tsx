/**
 * Bookshelves 列表页 (/orbit/bookshelves)
 * 显示所有 Bookshelf 分类，支持网格视图、列表视图、搜索、排序等功能
 */

"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useBookshelves, useCreateBookshelf, useDeleteBookshelf, useUpdateBookshelf } from "@/hooks/useBookshelf";
import { uploadBookshelfCover, pinBookshelf, unpinBookshelf } from "@/modules/orbit/domain/api";
import type { Bookshelf, BookshelfCreateRequest } from "@/modules/orbit/domain/bookshelves";
import {
  Plus, Search, Grid3x3, List, Star, MoreVertical, Edit2, Trash2,
  Archive, FolderOpen, Clock, BookOpen, Pin
} from "lucide-react";

type ViewMode = "grid" | "list";

export default function BookshelvesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQ, setSearchQ] = useState("");
  const [status, setStatus] = useState<"active" | "archived" | "all">("active");
  const [sortBy, setSortBy] = useState("-created_at");
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [showMenu, setShowMenu] = useState<string | null>(null);
  const [pinning, setPinning] = useState<string | null>(null);

  // 新建表单
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newIcon, setNewIcon] = useState("");
  const [newColor, setNewColor] = useState("#3b82f6");

  // 编辑表单
  const [editId, setEditId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editIcon, setEditIcon] = useState("");
  const [editColor, setEditColor] = useState("#3b82f6");

  // 封面图
  const [newCoverFile, setNewCoverFile] = useState<File | null>(null);
  const [newCoverPreview, setNewCoverPreview] = useState<string>("");
  const [editCoverFile, setEditCoverFile] = useState<File | null>(null);
  const [editCoverPreview, setEditCoverPreview] = useState<string>("");

  const { data: bookshelves = [], isLoading, refetch } = useBookshelves({
    status,
    sortBy: sortBy as any,
  });

  const createMutation = useCreateBookshelf();
  const updateMutation = useUpdateBookshelf();
  const deleteMutation = useDeleteBookshelf();

  // 过滤搜索 + 排序（置顶优先）
  const filtered = useMemo(() => {
    const searchFiltered = bookshelves.filter((b) =>
      b.name.toLowerCase().includes(searchQ.toLowerCase()) ||
      b.description?.toLowerCase().includes(searchQ.toLowerCase())
    );

    // 分离置顶和非置顶的
    const pinned = searchFiltered.filter((b) => b.isPinned);
    const unpinned = searchFiltered.filter((b) => !b.isPinned);

    // 置顶的按 pinnedAt 从新到旧排序
    pinned.sort((a, b) => {
      const aTime = new Date(a.pinnedAt || 0).getTime();
      const bTime = new Date(b.pinnedAt || 0).getTime();
      return bTime - aTime;
    });

    // 合并
    return [...pinned, ...unpinned];
  }, [bookshelves, searchQ]);

  const handleCreate = async () => {
    if (!newName.trim()) return;

    try {
      // 先创建书架
      const bs = await createMutation.mutateAsync({
        name: newName,
        description: newDescription,
        icon: newIcon,
        color: newColor,
      } as BookshelfCreateRequest);

      console.log("[CREATE] 书架创建成功:", bs.id);

      // 如果有新的封面图文件，上传封面图
      if (newCoverFile) {
        try {
          console.log("[CREATE] 开始上传封面图...");
          const result = await uploadBookshelfCover(bs.id, newCoverFile);
          console.log("[CREATE] 封面图上传成功，URL:", result.url);

          // 上传后，更新书架的 cover_url 到数据库
          console.log("[CREATE] 开始更新数据库中的 cover_url...");
          const updateResult = await updateMutation.mutateAsync({
            id: bs.id,
            payload: {
              name: bs.name,
              description: bs.description,
              icon: bs.icon,
              color: bs.color,
              coverUrl: result.url,  // ← 使用 coverUrl 而不是 cover_url
            } as BookshelfCreateRequest,
          });
          console.log("[CREATE] 数据库更新成功:", updateResult);
        } catch (error) {
          console.error("[CREATE] 上传或保存封面图失败:", error);
          // 即使失败也继续，不中断创建过程
        }
      }

      console.log("[CREATE] 表单清空，关闭对话框");
      setNewName("");
      setNewDescription("");
      setNewIcon("");
      setNewColor("#3b82f6");
      setNewCoverFile(null);
      setNewCoverPreview("");
      setCreating(false);
    } catch (error) {
      console.error("[CREATE] 创建失败:", error);
    }
  };  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除此 Bookshelf？其中的 Notes 将变为自由 Notes。")) return;

    try {
      await deleteMutation.mutateAsync({ id, cascade: "orphan" });
      setDeleting(null);
    } catch (error) {
      console.error("删除失败:", error);
    }
  };

  const handleEditOpen = (bs: Bookshelf) => {
    setEditId(bs.id);
    setEditName(bs.name);
    setEditDescription(bs.description || "");
    setEditIcon(bs.icon || "");
    setEditColor(bs.color || "#3b82f6");
    setEditCoverPreview(bs.coverUrl || "");  // 修改：使用 coverUrl 而不是 cover_url
    setEditCoverFile(null);
    setEditing(bs.id);
    setShowMenu(null);
  };

  const handleEditSave = async () => {
    if (!editId || !editName.trim()) return;

    try {
      // 如果有新的封面图文件，先上传
      let coverUrl = editCoverPreview;
      if (editCoverFile) {
        try {
          console.log("[EDIT] 开始上传新的封面图...");
          const result = await uploadBookshelfCover(editId, editCoverFile);
          coverUrl = result.url;
          console.log("[EDIT] 封面图上传成功，新 URL:", coverUrl);
        } catch (error) {
          console.error("[EDIT] 上传封面图失败:", error);
          // 继续，使用原来的 URL
        }
      }

      console.log("[EDIT] 开始更新书架...");
      const updateResult = await updateMutation.mutateAsync({
        id: editId,
        payload: {
          name: editName,
          description: editDescription,
          icon: editIcon,
          color: editColor,
          coverUrl: coverUrl,  // ← 使用 coverUrl 而不是 cover_url
        } as BookshelfCreateRequest,
      });
      console.log("[EDIT] 书架更新成功:", updateResult);

      setEditing(null);
      setEditId(null);
      setEditCoverFile(null);
    } catch (error) {
      console.error("[EDIT] 更新失败:", error);
    }
  };

  const handleRowClick = (id: string) => {
    router.push(`/orbit/bookshelves/${id}`);
  };

  const handlePin = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setPinning(id);
    try {
      await pinBookshelf(id);
      await refetch();
    } catch (error) {
      console.error("[PIN] 置顶失败:", error);
    } finally {
      setPinning(null);
    }
  };

  const handleUnpin = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setPinning(id);
    try {
      await unpinBookshelf(id);
      await refetch();
    } catch (error) {
      console.error("[UNPIN] 取消置顶失败:", error);
    } finally {
      setPinning(null);
    }
  };

  return (
    <div className="h-full w-full bg-gradient-to-br from-slate-50 to-slate-100 p-6">
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
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 max-h-96 overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">创建新书架</h2>
            <div className="space-y-4">
              {/* 封面图上传 */}
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-2">封面图（可选）</label>
                <div className="flex gap-2">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setNewCoverFile(file);
                        const reader = new FileReader();
                        reader.onload = (event) => {
                          setNewCoverPreview(event.target?.result as string);
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
                {newCoverPreview && (
                  <img src={newCoverPreview} alt="preview" className="mt-2 h-24 w-24 object-cover rounded-lg" />
                )}
              </div>

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
                  setNewCoverFile(null);
                  setNewCoverPreview("");
                }}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition"
              >
                取消
              </button>
              <button
                onClick={() => {
                  // 先上传封面图，再创建书架
                  handleCreate();
                }}
                disabled={!newName.trim() || createMutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {createMutation.isPending ? "创建中..." : "创建"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑对话框 */}
      {editing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 max-h-96 overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">编辑书架</h2>
            <div className="space-y-4">
              {/* 封面图上传 */}
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-2">封面图（可选）</label>
                <div className="flex gap-2">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setEditCoverFile(file);
                        const reader = new FileReader();
                        reader.onload = (event) => {
                          setEditCoverPreview(event.target?.result as string);
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
                {editCoverPreview && (
                  <img src={editCoverPreview} alt="preview" className="mt-2 h-24 w-24 object-cover rounded-lg" />
                )}
              </div>

              <input
                type="text"
                placeholder="书架名称（必填）"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <textarea
                placeholder="描述（可选）"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
              <input
                type="text"
                placeholder="图标名称（如：BookOpen, FolderOpen）"
                value={editIcon}
                onChange={(e) => setEditIcon(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-slate-700">颜色：</label>
                <input
                  type="color"
                  value={editColor}
                  onChange={(e) => setEditColor(e.target.value)}
                  className="w-16 h-10 rounded cursor-pointer"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setEditing(null);
                  setEditId(null);
                  setEditCoverFile(null);
                }}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition"
              >
                取消
              </button>
              <button
                onClick={handleEditSave}
                disabled={!editName.trim() || updateMutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {updateMutation.isPending ? "保存中..." : "保存"}
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
              className="relative bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer overflow-hidden group h-96"
              style={{
                borderTop: `4px solid ${bs.color || "#3b82f6"}`,
              }}
            >
              {/* 背景封面图 - 铺满整个卡片 */}
              {bs.coverUrl && (
                <img
                  src={bs.coverUrl}
                  alt="cover"
                  className="absolute inset-0 w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              )}

              {/* 渐变遮罩层 - 确保文字可读 */}
              <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60"></div>

              {/* 内容层 - 浮在图片上 */}
              <div className="absolute inset-0 p-6 flex flex-col justify-between">
                {/* 置顶徽章 */}
                {bs.isPinned && (
                  <div className="absolute top-3 left-3 bg-red-500 text-white p-2 rounded-lg shadow-md z-20">
                    <Pin size={16} fill="currentColor" />
                  </div>
                )}
                {/* 顶部菜单栏（浮动，鼠标靠近显示） */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex gap-1">
                  <div className="flex gap-1 bg-white rounded-lg shadow-md p-1 ml-auto">
                    <button
                      onClick={(e) =>
                        bs.isPinned ? handleUnpin(bs.id, e) : handlePin(bs.id, e)
                      }
                      disabled={pinning === bs.id}
                      className="p-2 text-slate-600 hover:bg-amber-50 hover:text-amber-600 rounded transition disabled:opacity-50"
                      title={bs.isPinned ? "取消置顶" : "置顶"}
                    >
                      <Pin
                        size={16}
                        fill={bs.isPinned ? "currentColor" : "none"}
                      />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditOpen(bs);
                      }}
                      className="p-2 text-slate-600 hover:bg-blue-50 hover:text-blue-600 rounded transition"
                      title="编辑"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(bs.id);
                      }}
                      className="p-2 text-slate-600 hover:bg-red-50 hover:text-red-600 rounded transition"
                      title="删除"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                {/* 底部标题和统计信息 */}
                <div>
                  <h3 className="text-xl font-semibold text-white mb-1">{bs.name}</h3>
                  {bs.description && (
                    <p className="text-sm text-gray-100 line-clamp-2 mb-3">{bs.description}</p>
                  )}

                  {/* 统计 */}
                  <div className="flex gap-4 text-sm text-gray-100">
                    <div className="flex items-center gap-1">
                      <FileText size={16} />
                      <span>{bs.noteCount} Notes</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Zap size={16} />
                      <span>{bs.usageCount} 次</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        // 列表视图 - 卡片式布局
        <div className="space-y-4">
          {filtered.map((bs) => (
            <div
              key={bs.id}
              onClick={() => handleRowClick(bs.id)}
              className="relative flex gap-4 bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer overflow-hidden group p-4"
              style={{
                borderLeft: `4px solid ${bs.color || "#3b82f6"}`,
              }}
            >
              {/* 左侧：封面图 - 更大的预览，带阴影和立体感 */}
              <div className="flex-shrink-0">
                {/* 置顶徽章 */}
                {bs.isPinned && (
                  <div className="absolute top-3 left-3 bg-red-500 text-white p-2 rounded-lg shadow-md z-20">
                    <Pin size={16} fill="currentColor" />
                  </div>
                )}
                {bs.coverUrl ? (
                  <div className="relative w-40 h-56 bg-slate-100 rounded-xl overflow-hidden flex items-center justify-center shadow-lg hover:shadow-2xl transition-all group/cover">
                    <img
                      src={bs.coverUrl}
                      alt="cover"
                      className="w-full h-full object-cover group-hover/cover:scale-110 transition-transform duration-300"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                      }}
                    />
                    {/* 顶部光泽效果 */}
                    <div className="absolute top-0 left-0 right-0 h-1/3 bg-gradient-to-b from-white/20 to-transparent pointer-events-none rounded-t-xl"></div>
                  </div>
                ) : (
                  <div className="w-40 h-56 bg-gradient-to-br from-slate-200 via-slate-300 to-slate-400 rounded-xl flex items-center justify-center shadow-lg hover:shadow-2xl transition-shadow">
                    <BookOpen size={48} className="text-slate-400 opacity-70" />
                  </div>
                )}
              </div>

              {/* 中间：标题和描述 */}
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-slate-900 mb-1 truncate">{bs.name}</h3>
                {bs.description && (
                  <p className="text-sm text-slate-600 line-clamp-3">{bs.description}</p>
                )}
              </div>

              {/* 右侧：菜单栏（浮动，鼠标靠近显示） */}
              <div
                className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10"
              >
                <div className="flex gap-1 bg-white rounded-lg shadow-md border border-slate-200 p-1">
                  <button
                    onClick={(e) =>
                      bs.isPinned ? handleUnpin(bs.id, e) : handlePin(bs.id, e)
                    }
                    disabled={pinning === bs.id}
                    className="p-2 text-slate-600 hover:bg-amber-50 hover:text-amber-600 rounded transition disabled:opacity-50"
                    title={bs.isPinned ? "取消置顶" : "置顶"}
                  >
                    <Pin
                      size={16}
                      fill={bs.isPinned ? "currentColor" : "none"}
                    />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditOpen(bs);
                    }}
                    className="p-2 text-slate-600 hover:bg-blue-50 hover:text-blue-600 rounded transition"
                    title="编辑"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(bs.id);
                    }}
                    className="p-2 text-slate-600 hover:bg-red-50 hover:text-red-600 rounded transition"
                    title="删除"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              {/* 右下角：统计信息 */}
              <div className="absolute bottom-3 right-3">
                <div className="flex items-center gap-3 text-sm text-slate-600 bg-white/80 backdrop-blur px-2 py-1 rounded-lg">
                  <div className="flex items-center gap-1">
                    <Zap size={14} className="text-amber-500" />
                    <span className="font-medium">{bs.usageCount}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <FileText size={14} className="text-blue-500" />
                    <span className="font-medium">{bs.noteCount}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// 导入使用的 icon
import { FileText, Zap } from "lucide-react";
