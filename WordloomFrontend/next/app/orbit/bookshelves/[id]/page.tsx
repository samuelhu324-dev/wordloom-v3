/**
 * Bookshelf 详情页 (/orbit/bookshelves/[id])
 * 显示 Bookshelf 内的所有 Notes，支持查看、添加、移除 Notes
 */

"use client";

import { useState, useMemo, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useBookshelf, useBookshelfNotes, useRemoveNoteFromBookshelf, useIncrementBookshelfUsage } from "@/hooks/useBookshelf";
import { incrementNoteUsage, createNote, pinNote, unpinNote } from "@/modules/orbit/domain/api";
import { useQueryClient } from "@tanstack/react-query";
import type { Note } from "@/modules/orbit/domain/notes";
import {
  ArrowLeft, Search, Grid3x3, List, Trash2, MoreVertical, Plus, Edit2,
  BookOpen, Clock, Zap, FileText, AlertCircle, Pin, Image as ImageIcon
} from "lucide-react";
import { NotePreviewPicker } from "@/components/NotePreviewPicker";

type ViewMode = "grid" | "list";

export default function BookshelfDetailPage() {
  const params = useParams();
  const router = useRouter();
  const qc = useQueryClient();
  const bookshelfId = params.id as string;

  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQ, setSearchQ] = useState("");
  const [sortBy, setSortBy] = useState("-created_at");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creatingNote, setCreatingNote] = useState(false);
  const [newNoteTitle, setNewNoteTitle] = useState("");
  const [removing, setRemoving] = useState<string | null>(null);
  const [showHeaderMenu, setShowHeaderMenu] = useState(false);
  const [pinning, setPinning] = useState<string | null>(null);
  const [showPreviewPicker, setShowPreviewPicker] = useState(false);
  const [previewPickerNote, setPreviewPickerNote] = useState<Note | null>(null);
  const [settingPreview, setSettingPreview] = useState(false);

  // 获取 Bookshelf 详情
  const { data: bookshelf, isLoading: bsLoading, refetch: refetchBookshelf } = useBookshelf(bookshelfId);

  // 获取 Bookshelf 内的 Notes
  const { data: notesInShelf = [], isLoading: notesLoading, refetch: refetchNotes } = useBookshelfNotes(bookshelfId, {
    sortBy: sortBy as any,
  });

  const removeMutation = useRemoveNoteFromBookshelf();
  const incrementMutation = useIncrementBookshelfUsage();

  // 对标签进行字母排序的辅助函数
  const getSortedTags = (tags: any[] | undefined) => {
    if (!tags || tags.length === 0) return [];
    return [...tags].sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  };

  // 页面可见性变化时刷新数据（用户编辑完note返回时）
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log("[SHELF] 页面变为可见，刷新数据");
        refetchBookshelf();
        refetchNotes();
      }
    };

    // 同时监听 focus 和 visibilitychange 事件
    window.addEventListener("focus", handleVisibilityChange);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("focus", handleVisibilityChange);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [refetchBookshelf, refetchNotes]);

  // 每次进入页面时刷新数据（最可靠的方式）
  useEffect(() => {
    console.log("[SHELF] 页面进入/bookshelfId 变化，刷新数据");
    refetchBookshelf();
    refetchNotes();
  }, [bookshelfId, refetchBookshelf, refetchNotes]);

  // 过滤搜索
  const filteredNotes = useMemo(() => {
    const filtered = notesInShelf.filter((n) =>
      n.title?.toLowerCase().includes(searchQ.toLowerCase()) ||
      n.text?.toLowerCase().includes(searchQ.toLowerCase())
    );

    // 调试：打印笔记数据
    if (filtered.length > 0) {
      console.log('[SHELF] 笔记列表:', filtered.slice(0, 2).map(n => ({
        id: n.id,
        title: n.title,
        preview_image: (n as any).preview_image,
        previewImage: n.previewImage,
      })));
    }

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
  }, [notesInShelf, searchQ]);

  const handleRemoveNote = async (noteId: string) => {
    if (!confirm("确定要从此书架中移除该 Note？")) return;

    try {
      await removeMutation.mutateAsync({ bookshelfId, noteId });
      setRemoving(null);
    } catch (error) {
      console.error("移除失败:", error);
    }
  };

  const handleCreateNote = async () => {
    if (!newNoteTitle.trim()) {
      alert("请输入 Note 标题");
      return;
    }

    setCreatingNote(true);
    try {
      // 创建笔记时直接传递 bookshelfId，文件夹会在后端自动创建到正确位置
      const newNote = await createNote({
        title: newNoteTitle,
        text: "",
        bookshelfId: bookshelfId,  // 直接在创建时指定所属书架
      });

      // 刷新列表
      await refetchNotes();

      setShowCreateModal(false);
      setNewNoteTitle("");

      // 进入编辑页面
      router.push(`/orbit/${newNote.id}`);
    } catch (err) {
      console.error("创建失败:", err);
      alert("创建失败，请重试");
    } finally {
      setCreatingNote(false);
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
    // 增加书架使用次数
    handleUseBookshelf();

    // 增加笔记使用次数
    try {
      incrementNoteUsage(noteId).catch(err => console.error("更新笔记使用次数失败:", err));
    } catch (error) {
      console.error("更新笔记使用次数失败:", error);
    }

    router.push(`/orbit/${noteId}`);
  };

  async function onPin(noteId: string, e: React.MouseEvent) {
    e.stopPropagation();
    setPinning(noteId);
    try {
      await pinNote(noteId);
      await refetchNotes();
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
      await refetchNotes();
    } catch (err) {
      console.error("[UNPIN] 取消置顶失败:", err);
    } finally {
      setPinning(null);
    }
  }

  // 打开预览图选择器
  const openPreviewPicker = (note: Note, e: React.MouseEvent) => {
    e.stopPropagation();
    setPreviewPickerNote(note);
    setShowPreviewPicker(true);
  };

  // 封面图上传完成后更新本地状态
  const handlePreviewImageSelected = async (imageUrl: string) => {
    if (!previewPickerNote) return;

    try {
      console.log('[SHELF] 收到上传完成回调，imageUrl:', imageUrl);
      console.log('[SHELF] previewPickerNote.id:', previewPickerNote.id);

      // 立即刷新笔记列表以显示新的预览图
      // refetchNotes() 会获取最新的数据，包括更新后的 preview_image
      console.log('[SHELF] 调用 refetchNotes() 刷新笔记列表...');
      await refetchNotes();

      console.log('[SHELF] ✓ 预览图已更新');
      setShowPreviewPicker(false);
      setPreviewPickerNote(null);
    } catch (err) {
      console.error('[SHELF] ✗ 预览图更新失败:', err);
      alert(`更新失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
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
    <div className="h-full w-full bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.push("/orbit/bookshelves")}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4 transition"
        >
          <ArrowLeft size={20} />
          返回书架列表
        </button>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-6 relative group"
          style={{ borderLeftWidth: "8px", borderLeftColor: bookshelf.color || "#3b82f6" }}>
          <div className="flex items-start justify-between gap-6">
            {/* 左侧：Cover 缩略图 */}
            <div className="flex-shrink-0">
              {bookshelf.coverUrl ? (
                <div className="relative w-48 h-72 bg-slate-100 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-shadow">
                  <img
                    src={bookshelf.coverUrl}
                    alt="cover"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                </div>
              ) : (
                <div className="w-48 h-72 bg-gradient-to-br from-slate-200 to-slate-300 rounded-xl flex items-center justify-center shadow-lg hover:shadow-2xl transition-shadow">
                  <BookOpen size={64} className="text-slate-400" />
                </div>
              )}
            </div>

            {/* 右侧：信息 */}
            <div className="flex-1">
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
            </div>

            {/* 右上角：菜单按钮（Hover 时显示） */}
            <div className="flex-shrink-0 relative">
              <button
                onClick={() => setShowHeaderMenu(!showHeaderMenu)}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-2 hover:bg-slate-100 rounded-lg"
                title="选项"
              >
                <MoreVertical size={20} className="text-slate-600" />
              </button>

              {/* 下拉菜单 */}
              {showHeaderMenu && (
                <div className="absolute top-full right-0 mt-2 bg-white border border-slate-200 rounded-lg shadow-lg z-10 w-48">
                  <button
                    onClick={() => {
                      setShowCreateModal(true);
                      setShowHeaderMenu(false);
                    }}
                    className="w-full text-left px-4 py-3 hover:bg-slate-50 flex items-center gap-2 text-slate-700 hover:text-green-600 transition border-b border-slate-100"
                  >
                    <Plus size={18} />
                    新建 Note
                  </button>
                  <button
                    onClick={() => {
                      router.push(`/orbit/bookshelves/${bookshelfId}?edit=1`);
                      setShowHeaderMenu(false);
                    }}
                    className="w-full text-left px-4 py-3 hover:bg-slate-50 flex items-center gap-2 text-slate-700 hover:text-blue-600 transition border-b border-slate-100"
                  >
                    <Edit2 size={18} />
                    编辑书架
                  </button>
                  <button
                    onClick={() => {
                      if (confirm("确定要删除此书架？其中的 Notes 将变为自由 Notes。")) {
                        // 调用删除函数
                        router.push("/orbit/bookshelves");
                      }
                      setShowHeaderMenu(false);
                    }}
                    className="w-full text-left px-4 py-3 hover:bg-red-50 flex items-center gap-2 text-slate-700 hover:text-red-600 transition"
                  >
                    <Trash2 size={18} />
                    删除书架
                  </button>
                </div>
              )}
            </div>
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

      {/* 新建 Note 对话框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold mb-6">新建 Note</h2>
            <input
              type="text"
              placeholder="输入 Note 标题..."
              value={newNoteTitle}
              onChange={(e) => setNewNoteTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleCreateNote();
                }
              }}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-6"
              autoFocus
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewNoteTitle("");
                }}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition"
              >
                取消
              </button>
              <button
                onClick={handleCreateNote}
                disabled={creatingNote || !newNoteTitle.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {creatingNote ? "创建中..." : "创建"}
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
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            新建 Note
          </button>
        </div>
      ) : viewMode === "grid" ? (
        // 网格视图
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredNotes.map((note) => (
            <div
              key={note.id}
              onClick={() => handleNoteClick(note.id)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer overflow-hidden group flex flex-col"
            >
              {/* 预览图片 */}
              {(note.cover_image_url || note.previewImage) && (
                <div className="relative w-full h-40 bg-slate-100 overflow-hidden">
                  <img
                    src={note.cover_image_url || note.previewImage}
                    alt="preview"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    onLoad={() => {
                      console.log('[SHELF] 图片加载成功:', {
                        noteId: note.id,
                        src: note.cover_image_url || note.previewImage,
                      });
                    }}
                    onError={(e) => {
                      console.log('[SHELF] 图片加载失败:', {
                        noteId: note.id,
                        src: (e.target as HTMLImageElement).src,
                      });
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                </div>
              )}

              {/* 卡片内容 */}
              <div className="p-3 flex flex-col flex-1">
              {/* 标题 */}
              <div className="flex justify-between items-start mb-1 gap-2">
                <div className="flex items-center gap-1 flex-1">
                  {note.isPinned && (
                    <div className="bg-red-500 text-white p-1 rounded flex-shrink-0">
                      <Pin size={12} fill="currentColor" />
                    </div>
                  )}
                  <h3 className="text-sm font-semibold text-slate-900 flex-1 line-clamp-2">
                    {note.title || "无标题"}
                  </h3>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition flex-shrink-0">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openPreviewPicker(note, e);
                    }}
                    className="p-1 text-slate-400 hover:text-blue-600 transition"
                    title="设置封面图"
                  >
                    <ImageIcon size={16} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveNote(note.id);
                    }}
                    className="p-1 text-slate-400 hover:text-red-600 transition"
                    title="从书架中移除"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>                {/* 预览文本 - 显示摘要或预览文本 */}
                {(note.summary || note.preview_text || note.previewText) && (
                  <p className="text-xs text-slate-600 line-clamp-2 mb-2 whitespace-normal break-words">
                    {String(note.summary || note.preview_text || note.previewText)
                      .replace(/<[^>]*>/g, '') // 移除任何 HTML 标签
                      .slice(0, 120)} {/* 限制字符数 */}
                  </p>
                )}

                {/* 元数据行 - 优先级/紧急/使用 */}
                <div className="flex gap-3 text-xs text-slate-600 mb-2 py-1">
                  <span className="flex items-center gap-1">
                    <span className="font-medium">优先级:</span>
                    <span>{note.priority || 3}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">紧急:</span>
                    <span>{note.urgency || 3}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">使用:</span>
                    <span>{note.usageCount || note.usage_count || 0}</span>
                  </span>
                  <button
                    onClick={(e) =>
                      note.isPinned ? onUnpin(note.id, e) : onPin(note.id, e)
                    }
                    disabled={pinning === note.id}
                    className="ml-auto p-0.5 text-amber-600 hover:text-amber-700 opacity-0 group-hover:opacity-100 transition disabled:opacity-50"
                    title={note.isPinned ? "取消置顶" : "置顶"}
                  >
                    <Pin size={14} fill={note.isPinned ? "currentColor" : "none"} />
                  </button>
                </div>

                {/* 时间信息 - 仅显示日期，无"更新于"文字 */}
                <div className="text-xs text-slate-400 mb-2">
                  <span>
                    {note.updatedAt || note.updated_at
                      ? new Date(note.updatedAt || note.updated_at).toLocaleDateString('zh-CN')
                      : ''}
                  </span>
                </div>

                {/* 标签 - 放在底部 */}
                {(note.tags_rel || note.tagsRel) && (note.tags_rel || note.tagsRel)?.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {getSortedTags(note.tags_rel || note.tagsRel)?.map((tag: any) => (
                      <span
                        key={tag.id}
                        className="inline-flex items-center px-2 py-1 text-white rounded text-xs font-medium"
                        style={{ backgroundColor: tag.color || '#999' }}
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        // 列表视图 - 改为卡片列表
        <div className="space-y-3">
          {filteredNotes.map((note) => (
            <div
              key={note.id}
              onClick={() => handleNoteClick(note.id)}
              className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer overflow-hidden group flex gap-4 p-3"
            >
              {/* 左侧缩略图 */}
              {(note.cover_image_url || note.previewImage) ? (
                <div className="w-24 h-24 flex-shrink-0 bg-slate-100 rounded overflow-hidden">
                  <img
                    src={note.cover_image_url || note.previewImage}
                    alt="thumbnail"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                </div>
              ) : (
                <div className="w-24 h-24 flex-shrink-0 bg-slate-100 rounded flex items-center justify-center">
                  <FileText size={32} className="text-slate-300" />
                </div>
              )}

              {/* 右侧内容 */}
              <div className="flex-1 min-w-0">
                {/* 标题 */}
                <div className="flex justify-between items-start gap-2 mb-1">
                  <div className="flex items-center gap-1 flex-1">
                    {note.isPinned && (
                      <div className="bg-red-500 text-white p-1 rounded flex-shrink-0">
                        <Pin size={12} fill="currentColor" />
                      </div>
                    )}
                    <h3 className="text-sm font-semibold text-slate-900 line-clamp-1 flex-1">
                      {note.title || "无标题"}
                    </h3>
                  </div>
                  <button
                    onClick={(e) =>
                      note.isPinned ? onUnpin(note.id, e) : onPin(note.id, e)
                    }
                    disabled={pinning === note.id}
                    className="p-1 text-amber-600 hover:text-amber-700 opacity-0 group-hover:opacity-100 transition flex-shrink-0 disabled:opacity-50"
                    title={note.isPinned ? "取消置顶" : "置顶"}
                  >
                    <Pin size={14} fill={note.isPinned ? "currentColor" : "none"} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveNote(note.id);
                    }}
                    className="p-1 text-slate-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition flex-shrink-0"
                    title="从书架中移除"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                {/* 预览文本 - 显示摘要或预览文本 */}
                {(note.summary || note.preview_text || note.previewText) && (
                  <p className="text-xs text-slate-600 line-clamp-2 mb-2 whitespace-normal break-words">
                    {String(note.summary || note.preview_text || note.previewText)
                      .replace(/<[^>]*>/g, '')
                      .slice(0, 120)}
                  </p>
                )}

                {/* 元数据行 - 优先级/紧急/使用/日期 */}
                <div className="flex gap-3 text-xs text-slate-600 mb-2">
                  <span className="flex items-center gap-1">
                    <span className="font-medium">优先级:</span>
                    <span>{note.priority || 3}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">紧急:</span>
                    <span>{note.urgency || 3}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">使用:</span>
                    <span>{note.usageCount || note.usage_count || 0}</span>
                  </span>
                  <span className="text-slate-400">
                    {note.updatedAt || note.updated_at
                      ? new Date(note.updatedAt || note.updated_at).toLocaleDateString('zh-CN')
                      : ''}
                  </span>
                </div>

                {/* 标签 */}
                {(note.tags_rel || note.tagsRel) && (note.tags_rel || note.tagsRel)?.length > 0 && (
                  <div className="flex gap-1 flex-wrap">
                    {getSortedTags(note.tags_rel || note.tagsRel)?.map((tag: any) => (
                      <span
                        key={tag.id}
                        className="inline-flex items-center px-2 py-1 text-white rounded text-xs font-medium"
                        style={{ backgroundColor: tag.color || '#999' }}
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 预览图选择器对话框 */}
      <NotePreviewPicker
        note={previewPickerNote}
        isOpen={showPreviewPicker}
        onClose={() => {
          setShowPreviewPicker(false);
          setPreviewPickerNote(null);
        }}
        onPreviewUploaded={handlePreviewImageSelected}
      />
    </div>
  );
}
