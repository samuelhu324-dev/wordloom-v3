/**
 * 标签选择器组件
 *
 * 功能：
 * - 显示所有可用标签
 * - 允许选择和取消选择标签
 * - 显示已选择的标签
 * - 支持创建新标签
 */

"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listTags,
  createTag,
  deleteTag,
} from "@/modules/orbit/domain/tags";
import type { Tag } from "@/modules/orbit/domain/notes";
import { TagColorPicker } from "./TagColorPicker";
import {
  Zap, Bug, TrendingUp, Clock, CheckCircle2,
  BookOpen, Link2, FileText, Code2, Lightbulb,
  AlertTriangle, Star, Smile, Pause, Flame,
  Palette, CheckCircle, Lock, Compass
} from "lucide-react";

interface TagSelectorProps {
  selectedTags: Tag[];
  onTagsChange: (tags: Tag[]) => void;
}

export function TagSelector({ selectedTags, onTagsChange }: TagSelectorProps) {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [newTagForm, setNewTagForm] = useState({
    name: "",
    color: "#3B82F6",
    description: "",
    icon: "Zap" as string,
  });

  // 查询所有标签
  const { data: allTags = [], isLoading } = useQuery({
    queryKey: ["orbit", "tags", "all"],
    queryFn: () => listTags("alphabetic"),
  });

  // 过滤显示的标签
  const displayTags = allTags.filter(tag =>
    tag.name.toLowerCase().includes(search.toLowerCase())
  );

  // 创建新标签
  async function onCreateTag() {
    if (!newTagForm.name.trim()) return;
    setCreating(true);
    try {
      const tag = await createTag({
        name: newTagForm.name,
        color: newTagForm.color,
        description: newTagForm.description,
        icon: newTagForm.icon,
      });
      await qc.invalidateQueries({ queryKey: ["orbit", "tags"] });
      onTagsChange([...selectedTags, tag]);
      setNewTagForm({ name: "", color: "#3B82F6", description: "", icon: "Zap" });
      setShowCreateForm(false);
    } finally {
      setCreating(false);
    }
  }

  // 切换标签选择状态
  function toggleTag(tag: Tag) {
    const isSelected = selectedTags.some(t => t.id === tag.id);
    if (isSelected) {
      onTagsChange(selectedTags.filter(t => t.id !== tag.id));
    } else {
      onTagsChange([...selectedTags, tag]);
    }
  }

  // 移除标签（从已选中的标签中移除）
  function removeTag(tagId: string) {
    onTagsChange(selectedTags.filter(t => t.id !== tagId));
  }

  // 删除标签（从系统中删除）
  async function onDeleteTag(tagId: string) {
    if (!confirm("确定要删除这个标签吗？关联的 Note 将保留，但标签标记会被移除。")) {
      return;
    }

    setDeleting(tagId);
    try {
      await deleteTag(tagId);
      // 移除该标签（如果已选中）
      removeTag(tagId);
      // 刷新标签列表
      await qc.invalidateQueries({ queryKey: ["orbit", "tags"] });
    } catch (error) {
      console.error("删除标签失败:", error);
      alert("删除标签失败，请重试");
    } finally {
      setDeleting(null);
    }
  }

  if (isLoading) {
    return <div className="p-3 text-gray-500 text-sm">加载标签中…</div>;
  }

  return (
    <div className="space-y-4 border rounded p-5 bg-white shadow-sm w-full">
      {/* 已选择的标签 */}
      {selectedTags.length > 0 && (
        <div className="space-y-2">
          <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">已选择的标签</label>
          <div className="flex flex-wrap gap-3 bg-gray-50 p-4 rounded-lg border border-gray-200">
            {selectedTags.map(tag => (
              <div
                key={tag.id}
                className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium text-white"
                style={{ backgroundColor: tag.color }}
              >
                <span className="inline-flex items-center gap-1">
                  {renderIcon(tag.icon, "#FFFFFF", 16)}
                  {tag.name}
                </span>
                <button
                  onClick={() => removeTag(tag.id)}
                  className="ml-1 hover:opacity-80 font-bold"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 搜索框 */}
      <div>
        <input
          type="text"
          placeholder="搜索或添加标签…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
        />
      </div>

      {/* 可用标签列表 */}
      {displayTags.length > 0 && (
        <div className="space-y-2 max-h-80 overflow-y-auto bg-gray-50 rounded-lg p-4 border border-gray-200">
          {displayTags.map(tag => {
            const isSelected = selectedTags.some(t => t.id === tag.id);
            return (
              <div
                key={tag.id}
                className={`flex items-center gap-2 px-3 py-2 rounded text-sm transition ${
                  isSelected
                    ? "bg-blue-50 border border-blue-300"
                    : "hover:bg-gray-100 border border-transparent"
                }`}
              >
                <button
                  onClick={() => toggleTag(tag)}
                  className="flex-1 flex items-center gap-2"
                >
              <div className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 shadow-sm" style={{ backgroundColor: tag.color }}>
                {renderIcon(tag.icon, contrastColor(tag.color), 18)}
              </div>
                  <span className="flex-1 text-left font-medium">{tag.name}</span>
                  {isSelected && (
                    <span className="text-blue-600 font-bold">✓</span>
                  )}
                </button>
                <button
                  onClick={() => onDeleteTag(tag.id)}
                  disabled={deleting === tag.id}
                  className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50 px-2"
                  title="删除标签"
                >
                  {deleting === tag.id ? "删除中…" : "🗑"}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* 创建新标签按钮 */}
      {!showCreateForm && (
        <button
          onClick={() => setShowCreateForm(true)}
          className="w-full px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded border border-blue-200 transition"
        >
          + 创建新标签
        </button>
      )}

      {/* 创建新标签表单 */}
      {showCreateForm && (
        <div className="border-t pt-4 space-y-3 bg-blue-50 p-4 rounded">
          <input
            type="text"
            placeholder="标签名称"
            value={newTagForm.name}
            onChange={(e) => setNewTagForm({ ...newTagForm, name: e.target.value })}
            className="w-full px-2 py-1 border rounded text-sm"
          />
          <div>
            <label className="block text-xs text-gray-600 mb-1">选择颜色</label>
            <TagColorPicker
              value={newTagForm.color}
              onChange={(color) => setNewTagForm({ ...newTagForm, color })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">选择图标</label>
            <IconGrid value={newTagForm.icon} onChange={(icon) => setNewTagForm({ ...newTagForm, icon })} />
          </div>
          <div className="flex gap-2">
            <button
              onClick={onCreateTag}
              disabled={creating || !newTagForm.name.trim()}
              className="flex-1 px-2 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {creating ? "创建中…" : "创建"}
            </button>
            <button
              onClick={() => {
                setShowCreateForm(false);
                setNewTagForm({ name: "", color: "#3B82F6", description: "", icon: "Zap" });
              }}
              className="flex-1 px-2 py-1 bg-gray-300 text-gray-800 text-sm rounded hover:bg-gray-400"
            >
              取消
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ================= Helper: icon render & grid =================
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

function IconGrid({ value, onChange }: { value: string; onChange: (v: string)=>void }) {
  const icons = Object.keys(ICON_COMPONENTS);
  return (
    <div className="grid grid-cols-10 gap-2 p-2 bg-white rounded border">
      {icons.map((name) => (
        <button
          key={name}
          onClick={() => onChange(name)}
          className={`h-10 w-10 rounded border flex items-center justify-center transition ${value===name ? 'border-blue-500 bg-blue-100 shadow' : 'border-gray-300 hover:bg-gray-100'}`}
          title={name}
        >
          {renderIcon(name, '#111827', 16)}
        </button>
      ))}
    </div>
  );
}
