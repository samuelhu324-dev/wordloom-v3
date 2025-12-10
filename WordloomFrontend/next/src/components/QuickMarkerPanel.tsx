/**
 * QuickMarkerPanel - 快速标记面板
 * 支持：一键快速创建标记
 */
'use client';

import React, { useState } from 'react';
import {
  Play,
  Clock,
  Zap,
  Bug,
  Lightbulb,
  CheckCircle2,
  MessageSquare,
  AlertCircle,
} from 'lucide-react';
import {
  createCheckpointMarker,
  toISO8601,
} from '@/modules/orbit/domain/checkpoints';

interface QuickMarkerPanelProps {
  checkpointId: string;
  isReadOnly?: boolean;
  onMarkerCreated?: () => void;
}

// Lucide 图标列表
const ICON_SUGGESTIONS = [
  { name: 'Clock', icon: Clock, label: '⏱️' },
  { name: 'Zap', icon: Zap, label: '⚡' },
  { name: 'Bug', icon: Bug, label: '🐛' },
  { name: 'Lightbulb', icon: Lightbulb, label: '💡' },
  { name: 'CheckCircle2', icon: CheckCircle2, label: '✓' },
  { name: 'MessageSquare', icon: MessageSquare, label: '💬' },
  { name: 'AlertCircle', icon: AlertCircle, label: '⚠️' },
];

/**
 * 快速标记面板
 */
export function QuickMarkerPanel({
  checkpointId,
  isReadOnly = false,
  onMarkerCreated,
}: QuickMarkerPanelProps) {
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('Clock');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createMarker = async () => {
    if (!newTitle.trim()) {
      setError('请输入标记标题');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const now = new Date();

      await createCheckpointMarker(checkpointId, {
        title: newTitle,
        description: newDescription || undefined,
        started_at: toISO8601(now),
        ended_at: toISO8601(now),
        category: 'work',
        emoji: selectedIcon,
      });

      setNewTitle('');
      setNewDescription('');
      setSelectedIcon('Clock');
      onMarkerCreated?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建标记失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isReadOnly) return null;

  return (
    <div className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg">
      <h4 className="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-2">
        <Clock className="w-4 h-4" />
        快速标记
      </h4>

      {error && (
        <div className="mb-3 p-2 bg-red-100 border border-red-300 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {/* 标题输入 */}
        <input
          type="text"
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="标记标题（例：修复缓存问题）"
          onKeyPress={(e) => e.key === 'Enter' && createMarker()}
          className="w-full px-3 py-2 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
        />

        {/* 描述输入 */}
        <textarea
          value={newDescription}
          onChange={(e) => setNewDescription(e.target.value)}
          placeholder="描述（可选）"
          rows={2}
          className="w-full px-3 py-2 border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm resize-none"
        />

        {/* 图标选择 */}
        <div>
          <label className="text-xs font-medium text-gray-700 mb-2 block">
            选择图标
          </label>
          <div className="grid grid-cols-7 gap-2">
            {ICON_SUGGESTIONS.map((item) => {
              const IconComponent = item.icon;
              return (
                <button
                  key={item.name}
                  onClick={() => setSelectedIcon(item.name)}
                  className={`p-2 rounded transition ${
                    selectedIcon === item.name
                      ? 'bg-blue-500 text-white border-2 border-blue-600'
                      : 'bg-white text-gray-600 border border-gray-300 hover:border-blue-400'
                  }`}
                  title={item.label}
                >
                  <IconComponent className="w-5 h-5 mx-auto" />
                </button>
              );
            })}
          </div>
        </div>

        {/* 创建按钮 */}
        <button
          onClick={createMarker}
          disabled={isSubmitting}
          className="w-full px-3 py-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-1 transition"
        >
          <Play className="w-4 h-4" />
          开始
        </button>
      </div>
    </div>
  );
}
