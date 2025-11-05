/**
 * MarkerDialog - 高级标记编辑对话框
 * 支持：时间选择、标签管理、自定义 emoji/color
 */
'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  Clock,
  Save,
  AlertCircle,
  Trash2,
} from 'lucide-react';
import {
  CheckpointMarker,
  updateCheckpointMarker,
  deleteCheckpointMarker,
  CreateCheckpointMarkerRequest,
  toISO8601,
  parseISO8601,
  formatDuration,
} from '@/modules/orbit/domain/checkpoints';

interface MarkerDialogProps {
  marker?: CheckpointMarker; // 如果为空则是创建模式
  checkpointId: string;
  onClose: () => void;
  onSave: (marker: CheckpointMarker) => void;
  onDelete?: (markerId: string) => void;
}

// 图标选项 - 与QuickMarkerPanel保持一致
const ICON_OPTIONS = [
  { name: 'Clock', icon: '🕐' },
  { name: 'Zap', icon: '⚡' },
  { name: 'Bug', icon: '🐛' },
  { name: 'Lightbulb', icon: '💡' },
  { name: 'CheckCircle2', icon: '✓' },
  { name: 'MessageSquare', icon: '💬' },
  { name: 'AlertCircle', icon: '⚠️' },
];

/**
 * 高级标记编辑对话框
 */
export function MarkerDialog({
  marker,
  checkpointId,
  onClose,
  onSave,
  onDelete,
}: MarkerDialogProps) {
  const isEditMode = !!marker;

  // 表单状态
  const [title, setTitle] = useState(marker?.title || '');
  const [description, setDescription] = useState(marker?.description || '');
  const [startTime, setStartTime] = useState<Date>(
    marker ? parseISO8601(marker.started_at) : new Date()
  );
  const [endTime, setEndTime] = useState<Date>(
    marker ? parseISO8601(marker.ended_at) : new Date(Date.now() + 5 * 60000) // 默认 5 分钟
  );
  const [isCompleted, setIsCompleted] = useState(marker?.is_completed || false);
  const [emoji, setEmoji] = useState(marker?.emoji || 'Clock');

  // UI 状态
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const durationSeconds = Math.round((endTime.getTime() - startTime.getTime()) / 1000);
  const isValidDuration = durationSeconds > 0;

  const handleSave = async () => {
    if (!title.trim()) {
      setError('请输入标记标题');
      return;
    }

    if (!isValidDuration) {
      setError('结束时间必须晚于开始时间');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (isEditMode && marker) {
        // 更新现有标记
        const updated = await updateCheckpointMarker(checkpointId, marker.id, {
          title,
          description,
          started_at: toISO8601(startTime),
          ended_at: toISO8601(endTime),
          emoji,
          is_completed: isCompleted,
        });
        onSave(updated);
      } else {
        // 创建新标记
        const payload: CreateCheckpointMarkerRequest = {
          title,
          description,
          started_at: toISO8601(startTime),
          ended_at: toISO8601(endTime),
          emoji,
        };
        onSave(payload as unknown as CheckpointMarker);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!isEditMode || !marker) return;
    if (!confirm('确定要删除此标记吗？')) return;

    setIsLoading(true);
    try {
      await deleteCheckpointMarker(checkpointId, marker.id);
      onDelete?.(marker.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    } finally {
      setIsLoading(false);
    }
  };



  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white">
          <h2 className="text-xl font-semibold">
            {isEditMode ? '编辑标记' : '新建标记'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-100 border border-red-300 rounded-lg flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}

          {/* Title Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              标记标题 *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例：缓存修复完成"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>

          {/* Description Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              描述
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="添加更多详情..."
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
            />
          </div>

          {/* Time Selection */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4 inline mr-1" />
                开始时间
              </label>
              <input
                type="datetime-local"
                value={startTime.toISOString().slice(0, 16)}
                onChange={(e) => setStartTime(new Date(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4 inline mr-1" />
                结束时间
              </label>
              <input
                type="datetime-local"
                value={endTime.toISOString().slice(0, 16)}
                onChange={(e) => setEndTime(new Date(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
          </div>

          {/* Duration Display */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <span className="font-semibold">持续时间：</span>
              {isValidDuration ? formatDuration(durationSeconds) : '—— 无效时间 ——'}
            </p>
          </div>

          {/* Completion Status Toggle */}
          <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <input
              type="checkbox"
              id="isCompleted"
              checked={isCompleted}
              onChange={(e) => setIsCompleted(e.target.checked)}
              className="w-5 h-5 text-green-600 rounded cursor-pointer focus:ring-2 focus:ring-green-500"
            />
            <label htmlFor="isCompleted" className="flex-1 cursor-pointer">
              <span className="text-sm font-medium text-gray-700">
                ✓ 标记为已完成
              </span>
              <p className="text-xs text-gray-500 mt-1">
                勾选此项会增加检查点的完成度百分比
              </p>
            </label>
          </div>

          {/* Emoji Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              选择图标
            </label>
            <div className="grid grid-cols-7 gap-2">
              {ICON_OPTIONS.map((item) => (
                <button
                  key={item.name}
                  onClick={() => setEmoji(item.name)}
                  className={`p-3 rounded-lg border-2 transition text-lg ${
                    emoji === item.name
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {item.icon}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50 sticky bottom-0">
          <div className="flex gap-2">
            {isEditMode && onDelete && (
              <button
                onClick={handleDelete}
                disabled={isLoading}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white rounded-lg transition flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                删除
              </button>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg transition disabled:opacity-50"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading || !title.trim() || !isValidDuration}
              className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white rounded-lg transition flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {isLoading ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
