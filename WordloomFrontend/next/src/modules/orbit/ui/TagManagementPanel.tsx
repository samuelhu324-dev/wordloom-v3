/**
 * 标签管理面板组件
 *
 * 功能：
 * - 显示所有标签及其使用次数
 * - 创建新标签（带颜色选择）
 * - 编辑标签（名称、颜色、描述）
 * - 删除标签
 * - 搜索和排序标签
 */

"use client";

import { useState, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listTags,
  createTag,
  updateTag,
  deleteTag,
  type TagSort,
} from "@/modules/orbit/domain/tags";
import type { Tag } from "@/modules/orbit/domain/notes";
import { TagColorPicker } from "./TagColorPicker";

interface TagPanelProps {
  onTagSelect?: (tag: Tag) => void;
}

export function TagManagementPanel({ onTagSelect }: TagPanelProps) {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<TagSort>("frequency");
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  // 新建标签表单
  const [newTagForm, setNewTagForm] = useState({
    name: "",
    color: "#3B82F6",
    description: "",
  });

  // 编辑标签表单
  const [editForm, setEditForm] = useState<Partial<Tag> | null>(null);

  // 查询标签
  const { data: tags = [], isLoading } = useQuery({
    queryKey: ["orbit", "tags", { search, sort }],
    queryFn: () => listTags(sort, search),
  });

  // 创建标签
  async function onCreateTag() {
    if (!newTagForm.name.trim()) return;
    setCreating(true);
    try {
      const tag = await createTag({
        name: newTagForm.name,
        color: newTagForm.color,
        description: newTagForm.description,
      });
      await qc.invalidateQueries({ queryKey: ["orbit", "tags"] });
      setNewTagForm({ name: "", color: "#3B82F6", description: "" });
      onTagSelect?.(tag);
    } finally {
      setCreating(false);
    }
  }

  // 更新标签
  async function onUpdateTag() {
    if (!editForm || !editingId) return;
    try {
      const payload: Partial<{
        name: string;
        color: string;
        description: string;
      }> = {};
      if (editForm.name) payload.name = editForm.name;
      if (editForm.color) payload.color = editForm.color;
      if (editForm.description !== undefined)
        payload.description = editForm.description || "";

      await updateTag(editingId, payload);
      await qc.invalidateQueries({ queryKey: ["orbit", "tags"] });
      setEditingId(null);
      setEditForm(null);
    } catch (e) {
      console.error("Failed to update tag:", e);
    }
  }

  // 删除标签
  async function onDeleteTag(tagId: string) {
    if (!confirm("确定删除这个标签吗？")) return;
    setDeleting(tagId);
    try {
      await deleteTag(tagId);
      await qc.invalidateQueries({ queryKey: ["orbit", "tags"] });
    } finally {
      setDeleting(null);
    }
  }

  if (isLoading) return <div className="p-4 text-gray-500">加载中…</div>;

  return (
    <div className="space-y-6 p-4">
      {/* 标题 */}
      <div>
        <h2 className="text-lg font-semibold mb-2">标签管理</h2>
        <p className="text-sm text-gray-600">管理笔记标签，支持自定义颜色和描述</p>
      </div>

      {/* 搜索和排序 */}
      <div className="flex gap-3 flex-wrap">
        <input
          type="text"
          placeholder="搜索标签…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-48 px-3 py-2 border rounded text-sm"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as TagSort)}
          className="px-3 py-2 border rounded text-sm"
        >
          <option value="frequency">按频率</option>
          <option value="alphabetic">按字母</option>
          <option value="recent">按最新</option>
        </select>
      </div>

      {/* 创建新标签 */}
      <div className="border rounded p-4 bg-gray-50 space-y-3">
        <h3 className="font-semibold text-sm">新建标签</h3>
        <div className="space-y-2">
          <input
            type="text"
            placeholder="标签名称"
            value={newTagForm.name}
            onChange={(e) => setNewTagForm({ ...newTagForm, name: e.target.value })}
            className="w-full px-3 py-2 border rounded text-sm"
          />
          <textarea
            placeholder="标签描述（可选）"
            value={newTagForm.description}
            onChange={(e) =>
              setNewTagForm({ ...newTagForm, description: e.target.value })
            }
            className="w-full px-3 py-2 border rounded text-sm"
            rows={2}
          />
          <div>
            <label className="block text-xs text-gray-600 mb-2">选择颜色</label>
            <TagColorPicker
              value={newTagForm.color}
              onChange={(color) => setNewTagForm({ ...newTagForm, color })}
            />
          </div>
          <button
            onClick={onCreateTag}
            disabled={creating || !newTagForm.name.trim()}
            className="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {creating ? "创建中…" : "创建标签"}
          </button>
        </div>
      </div>

      {/* 标签列表 */}
      <div className="space-y-2">
        <h3 className="font-semibold text-sm">
          标签列表 ({tags.length})
        </h3>
        {tags.length === 0 ? (
          <div className="text-center py-6 text-gray-500 text-sm">暂无标签</div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {tags.map((tag) =>
              editingId === tag.id ? (
                // 编辑模式
                <div key={tag.id} className="border rounded p-3 bg-yellow-50 space-y-3">
                  <input
                    type="text"
                    value={editForm?.name || tag.name}
                    onChange={(e) =>
                      setEditForm({ ...editForm, name: e.target.value })
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                  />
                  <textarea
                    value={editForm?.description || tag.description || ""}
                    onChange={(e) =>
                      setEditForm({ ...editForm, description: e.target.value })
                    }
                    className="w-full px-2 py-1 border rounded text-sm"
                    rows={2}
                  />
                  <TagColorPicker
                    value={editForm?.color || tag.color}
                    onChange={(color) =>
                      setEditForm({ ...editForm, color })
                    }
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={onUpdateTag}
                      className="flex-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                    >
                      保存
                    </button>
                    <button
                      onClick={() => {
                        setEditingId(null);
                        setEditForm(null);
                      }}
                      className="flex-1 px-3 py-1 bg-gray-400 text-white rounded text-sm hover:bg-gray-500"
                    >
                      取消
                    </button>
                  </div>
                </div>
              ) : (
                // 显示模式
                <div
                  key={tag.id}
                  className="flex items-center justify-between p-3 border rounded hover:shadow-md transition"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div
                      className="w-4 h-4 rounded border border-gray-300"
                      style={{ backgroundColor: tag.color }}
                    />
                    <div className="flex-1">
                      <div className="font-semibold text-sm">{tag.name}</div>
                      {tag.description && (
                        <div className="text-xs text-gray-600">
                          {tag.description}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mr-3">
                    使用: {tag.count}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setEditingId(tag.id);
                        setEditForm(tag);
                      }}
                      className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => onDeleteTag(tag.id)}
                      disabled={deleting === tag.id}
                      className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600 disabled:opacity-50"
                    >
                      {deleting === tag.id ? "删中…" : "删除"}
                    </button>
                  </div>
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}
