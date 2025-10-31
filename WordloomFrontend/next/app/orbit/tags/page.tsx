"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listTags, createTag, deleteTag } from "@/modules/orbit/domain/tags";
import type { Tag } from "@/modules/orbit/domain/notes";
import { TagColorPicker } from "@/modules/orbit/ui/TagColorPicker";
import {
  Zap, Bug, TrendingUp, Clock, CheckCircle2,
  BookOpen, Link2, FileText, Code2, Lightbulb,
  AlertTriangle, Star, Smile, Pause, Flame,
  Palette, CheckCircle, Lock, Compass
} from "lucide-react";

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
    <div className="grid grid-cols-10 gap-1">
      {icons.map((name) => (
        <button
          key={name}
          onClick={() => onChange(name)}
          className={`h-8 w-8 rounded border flex items-center justify-center ${value===name ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-100'}`}
          title={name}
        >
          {renderIcon(name, '#111827', 16)}
        </button>
      ))}
    </div>
  );
}

export default function TagsManagementPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<'management'|'creation'>('management');
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<string|null>(null);
  const [form, setForm] = useState({ name: "", color: "#3B82F6", icon: "Zap", description: "" });

  const { data: all = [], isLoading } = useQuery({
    queryKey: ["orbit","tags","all"],
    queryFn: () => listTags("alphabetic"),
  });

  const filtered: Tag[] = useMemo(() => {
    if (!search) return all;
    const q = search.toLowerCase();
    return all.filter(t => t.name.toLowerCase().includes(q));
  }, [all, search]);

  async function onCreate() {
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      await createTag({ name: form.name, color: form.color, icon: form.icon, description: form.description });
      await qc.invalidateQueries({ queryKey: ["orbit","tags"] });
      setForm({ name: "", color: "#3B82F6", icon: "Zap", description: "" });
      setTab('management');
    } finally { setCreating(false); }
  }

  async function onDelete(id: string) {
    if (!confirm('确定删除该标签？')) return;
    setDeleting(id);
    try { await deleteTag(id); await qc.invalidateQueries({ queryKey: ["orbit","tags"] }); }
    finally { setDeleting(null); }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <button onClick={() => setTab('management')} className={`px-3 py-1 rounded border ${tab==='management' ? 'bg-white shadow' : 'bg-gray-100 hover:bg-white'}`}>Management</button>
        <button onClick={() => setTab('creation')} className={`px-3 py-1 rounded border ${tab==='creation' ? 'bg-white shadow' : 'bg-gray-100 hover:bg-white'}`}>Creation</button>
      </div>

      {tab === 'management' && (
        <div className="space-y-3">
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="搜索标签..." className="w-full px-3 py-2 border rounded" />
          {isLoading ? (
            <div className="text-sm text-gray-500">加载中…</div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {filtered.map(tag => (
                <div key={tag.id} className="border rounded p-2 bg-white flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded flex items-center justify-center" style={{ backgroundColor: tag.color }}>
                      {renderIcon(tag.icon, contrastColor(tag.color), 18)}
                    </div>
                    <div className="font-medium text-sm">{tag.name}</div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>使用 {tag.count}</span>
                    <button onClick={() => onDelete(tag.id)} disabled={deleting===tag.id} className="text-red-500 hover:text-red-700">{deleting===tag.id? '删除中…':'删除'}</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'creation' && (
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-600">预览</label>
            <div className="mt-1 inline-flex items-center gap-2 px-3 py-1 rounded" style={{ backgroundColor: form.color }}>
              {renderIcon(form.icon, contrastColor(form.color), 18)}
              <span className="text-white font-medium">{form.name || '标签名称'}</span>
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-600">标签名称</label>
            <input value={form.name} onChange={e=>setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 border rounded" />
          </div>
          <div>
            <label className="text-xs text-gray-600">选择颜色</label>
            <TagColorPicker value={form.color} onChange={(color)=>setForm({ ...form, color })} />
          </div>
          <div>
            <label className="text-xs text-gray-600">选择图标</label>
            <IconGrid value={form.icon} onChange={(icon)=>setForm({ ...form, icon })} />
          </div>
          <div className="flex gap-2">
            <button onClick={onCreate} disabled={creating || !form.name.trim()} className="px-3 py-2 bg-blue-600 text-white rounded disabled:opacity-50">{creating? '创建中…':'创建'}</button>
            <button onClick={()=>setForm({ name: '', color: '#3B82F6', icon: 'Zap', description: ''})} className="px-3 py-2 bg-gray-200 rounded">重置</button>
          </div>
        </div>
      )}
    </div>
  );
}
