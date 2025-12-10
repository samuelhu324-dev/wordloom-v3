/**
 * Checkpoint 管理组件
 * 用于在 Note 编辑页面中显示和管理检查点和标记
 */
'use client';

import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, Plus, Trash2, Clock, AlertCircle, Edit2, Zap, Bug, Lightbulb, CheckCircle2, MessageSquare } from 'lucide-react';
import {
  Checkpoint,
  CheckpointMarker,
  CheckpointDetail,
  createCheckpoint,
  createCheckpointMarker,
  updateCheckpoint,
  deleteCheckpoint,
  deleteCheckpointMarker,
  listCheckpoints,
  formatDuration,
  toISO8601,
} from '@/modules/orbit/domain/checkpoints';
import { useOrbitTags } from '@/hooks/useOrbitTags';
import { MarkerDialog } from './MarkerDialog';
import { QuickMarkerPanel } from './QuickMarkerPanel';
import { CheckpointStats } from './CheckpointStats';

interface CheckpointManagerProps {
  noteId: string;
  isReadOnly?: boolean;
  onCheckpointsChange?: (checkpoints: CheckpointDetail[]) => void;
}

/**
 * Checkpoint 管理器主组件
 */
export function CheckpointManager({
  noteId,
  isReadOnly = false,
  onCheckpointsChange,
}: CheckpointManagerProps) {
  const [checkpoints, setCheckpoints] = useState<CheckpointDetail[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNewCheckpointDialog, setShowNewCheckpointDialog] = useState(false);
  const [newCheckpointTitle, setNewCheckpointTitle] = useState('');
  const [newCheckpointTags, setNewCheckpointTags] = useState<string[]>([]);

  // 加载检查点
  useEffect(() => {
    loadCheckpoints();
  }, [noteId]);

  const loadCheckpoints = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await listCheckpoints(noteId);
      setCheckpoints(data);
      onCheckpointsChange?.(data);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load checkpoints';
      setError(errorMsg);
      console.error('Failed to load checkpoints:', err);
      // 重要：只记录错误，不崩溃应用
      // Checkpoint 功能是可选的，即使失败也不应影响 Note 编辑
      setCheckpoints([]); // 设为空数组，这样 UI 就不会显示错误
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCheckpoint = async () => {
    // 标题允许为空，使用时间戳作为默认名称
    const finalTitle = newCheckpointTitle.trim() || `检查点 ${new Date().toLocaleTimeString('zh-CN')}`;

    setIsLoading(true);
    setError(null);

    try {
      const newCheckpoint = await createCheckpoint(noteId, {
        title: finalTitle,
        tags: [],  // 清空tags，每次创建都是干净的
      });

      // 更新本地checkpoints列表
      setCheckpoints(prev => [...prev, { ...newCheckpoint, markers: [] }]);

      // 重置表单 - 这是关键！确保下次创建是干净的
      setShowNewCheckpointDialog(false);
      setNewCheckpointTitle('');
      setNewCheckpointTags([]);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create checkpoint');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteCheckpoint = async (checkpointId: string) => {
    if (!confirm('Delete this checkpoint?')) return;

    try {
      await deleteCheckpoint(checkpointId);
      setCheckpoints(checkpoints.filter((c) => c.id !== checkpointId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete checkpoint');
    }
  };

  return (
    <div className="border-t pt-4 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Clock className="w-5 h-5" />
          检查点（Checkpoints）
        </h3>
        {!isReadOnly && (
          <button
            onClick={() => {
              // 打开对话框前，确保表单状态是干净的
              setNewCheckpointTitle('');
              setNewCheckpointTags([]);
              setError(null);
              setShowNewCheckpointDialog(true);
            }}
            disabled={isLoading}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 flex items-center gap-1"
          >
            <Plus className="w-4 h-4" />
            新建
          </button>
        )}
      </div>

      {/* 新建 Checkpoint 对话框 */}
      {showNewCheckpointDialog && (
        <NewCheckpointDialog
          onClose={() => {
            setShowNewCheckpointDialog(false);
            setNewCheckpointTitle('');
            setNewCheckpointTags([]);
          }}
          onSave={handleAddCheckpoint}
          title={newCheckpointTitle}
          onTitleChange={setNewCheckpointTitle}
          selectedTags={newCheckpointTags}
          onTagsChange={setNewCheckpointTags}
          isLoading={isLoading}
        />
      )}

      {error && !error.includes('404') && (
        <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-4 text-gray-500">加载中...</div>
      ) : checkpoints.length === 0 ? (
        <div className="text-center py-4 text-gray-400">
          还没有检查点。{!isReadOnly && '点击"新建"添加第一个。'}
        </div>
      ) : (
        <div className="space-y-2">
          {checkpoints.map((checkpoint) => (
            <CheckpointItem
              key={checkpoint.id}
              checkpoint={checkpoint}
              isExpanded={expandedId === checkpoint.id}
              onToggleExpand={() =>
                setExpandedId(expandedId === checkpoint.id ? null : checkpoint.id)
              }
              onDelete={() => handleDeleteCheckpoint(checkpoint.id)}
              onReload={loadCheckpoints}
              isReadOnly={isReadOnly}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Checkpoint Item 组件
// ============================================================================

interface CheckpointItemProps {
  checkpoint: CheckpointDetail;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onDelete: () => void;
  onReload: () => void;
  isReadOnly?: boolean;
}

function CheckpointItem({
  checkpoint,
  isExpanded,
  onToggleExpand,
  onDelete,
  onReload,
  isReadOnly = false,
}: CheckpointItemProps) {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState(checkpoint.title);
  const [showQuickMarkerModal, setShowQuickMarkerModal] = useState(false);
  const [isSavingTitle, setIsSavingTitle] = useState(false);
  const { tags: allTags } = useOrbitTags();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'on_hold':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleTitleSave = async () => {
    if (editedTitle.trim() === checkpoint.title) {
      setIsEditingTitle(false);
      return;
    }

    setIsSavingTitle(true);
    try {
      await updateCheckpoint(checkpoint.id, { title: editedTitle.trim() });
      setIsEditingTitle(false);
      onReload();
    } catch (err) {
      console.error('Failed to update title:', err);
      setEditedTitle(checkpoint.title);
    } finally {
      setIsSavingTitle(false);
    }
  };

  return (
    <div className="border rounded-lg">
      <div
        onClick={onToggleExpand}
        className="p-3 bg-gray-50 hover:bg-gray-100 cursor-pointer flex items-center justify-between"
      >
        <div className="flex items-center gap-3 flex-1">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
          <div className="flex-1">
            {/* 可编辑的标题 */}
            {isEditingTitle ? (
              <input
                autoFocus
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                onBlur={handleTitleSave}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') handleTitleSave();
                }}
                onClick={(e) => e.stopPropagation()}
                className="font-medium border border-blue-400 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isSavingTitle}
              />
            ) : (
              <h4
                className="font-medium cursor-pointer hover:text-blue-600"
                onDoubleClick={(e) => {
                  e.stopPropagation();
                  setIsEditingTitle(true);
                }}
              >
                {checkpoint.title}
              </h4>
            )}
            <div className="text-sm text-gray-600 flex items-center gap-3 mt-1">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(checkpoint.status)}`}>
                {checkpoint.status}
              </span>
              <span className="text-xs">
                共 <span className="font-bold">{checkpoint.markers.length}</span> 标记
              </span>
            </div>
            {/* 标签显示 */}
            {checkpoint.tags && checkpoint.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {checkpoint.tags.map((tagId) => {
                  const tag = allTags?.find((t: any) => t.id === tagId);
                  return tag ? (
                    <span
                      key={tagId}
                      className="px-3 py-1 rounded-full text-xs font-semibold text-white shadow-sm hover:shadow-md transition transform hover:scale-105"
                      style={{
                        backgroundColor: tag.color,
                        opacity: 0.9,
                      }}
                    >
                      {tag.name}
                    </span>
                  ) : null;
                })}
              </div>
            )}
          </div>
        </div>

        {!isReadOnly && (
          <div className="flex items-center gap-3">
            {/* 统计信息 Hover 浮窗 */}
            <CheckpointStats checkpoint={checkpoint} />

            {/* 快速标记按钮 */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowQuickMarkerModal(true);
              }}
              className="p-1 text-blue-500 hover:bg-blue-100 rounded"
              title="快速标记"
            >
              <Clock className="w-4 h-4" />
            </button>

            {/* 删除按钮 */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 text-red-500 hover:bg-red-100 rounded"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* 快速标记 Modal */}
        {showQuickMarkerModal && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowQuickMarkerModal(false)}
          >
            <div
              className="bg-white rounded-lg shadow-xl p-4 w-96 max-h-96 overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">快速标记</h3>
                <button
                  onClick={() => setShowQuickMarkerModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <QuickMarkerPanel
                checkpointId={checkpoint.id}
                isReadOnly={false}
                onMarkerCreated={() => {
                  setShowQuickMarkerModal(false);
                  onReload();
                }}
              />
            </div>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="p-4 border-t space-y-4">
          {checkpoint.description && (
            <p className="text-sm text-gray-600">{checkpoint.description}</p>
          )}

          <CheckpointMarkerList
            checkpoint={checkpoint}
            onReload={onReload}
            isReadOnly={isReadOnly}
          />
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Marker List 组件
// ============================================================================

interface CheckpointMarkerListProps {
  checkpoint: CheckpointDetail;
  onReload: () => void;
  isReadOnly?: boolean;
}

function CheckpointMarkerList({
  checkpoint,
  onReload,
  isReadOnly = false,
}: CheckpointMarkerListProps) {
  const [markers, setMarkers] = useState(checkpoint.markers);
  const [selectedMarkerForEdit, setSelectedMarkerForEdit] = useState<CheckpointMarker | null>(null);
  const [showMarkerDialog, setShowMarkerDialog] = useState(false);
  const [isAddingMarker, setIsAddingMarker] = useState(false);

  const handleAddMarker = async () => {
    setIsAddingMarker(true);
    try {
      // 简单实现：创建当前时间的标记
      const now = new Date();
      const endTime = new Date(now.getTime() + 5 * 60000); // 默认 5 分钟

      const newMarker = await createCheckpointMarker(checkpoint.id, {
        title: '新标记',
        started_at: toISO8601(now),
        ended_at: toISO8601(endTime),
      });

      setMarkers([...markers, newMarker]);
    } catch (err) {
      console.error('Failed to create marker:', err);
    } finally {
      setIsAddingMarker(false);
    }
  };

  const handleDeleteMarker = async (markerId: string) => {
    if (!confirm('删除此标记?')) return;

    try {
      await deleteCheckpointMarker(checkpoint.id, markerId);
      setMarkers(markers.filter((m) => m.id !== markerId));
    } catch (err) {
      console.error('Failed to delete marker:', err);
    }
  };

  const handleMarkerSave = async (markerData: CheckpointMarker) => {
    try {
      if (selectedMarkerForEdit) {
        // 更新模式已在 MarkerDialog 中处理
        const updatedMarkers = markers.map((m) =>
          m.id === selectedMarkerForEdit.id ? markerData : m
        );
        setMarkers(updatedMarkers);
      } else {
        // 创建新标记
        const newMarker = await createCheckpointMarker(checkpoint.id, markerData as any);
        setMarkers([...markers, newMarker]);
      }
      setShowMarkerDialog(false);
      setSelectedMarkerForEdit(null);
    } catch (err) {
      console.error('Failed to save marker:', err);
    }
  };

  const handleEditMarker = (marker: CheckpointMarker) => {
    setSelectedMarkerForEdit(marker);
    setShowMarkerDialog(true);
  };

  return (
    <div>
      <div className="mb-3">
        <h5 className="font-medium text-sm">标记（Markers）</h5>
      </div>

      {markers.length === 0 ? (
        <p className="text-xs text-gray-400">暂无标记</p>
      ) : (
        <div className="space-y-2 bg-white p-2 rounded border border-gray-200">
          {markers.map((marker) => (
            <MarkerRow
              key={marker.id}
              marker={marker}
              checkpointId={checkpoint.id}
              onDelete={() => handleDeleteMarker(marker.id)}
              onEdit={() => handleEditMarker(marker)}
              isReadOnly={isReadOnly}
            />
          ))}
        </div>
      )}

      {/* Marker Dialog */}
      {showMarkerDialog && (
        <MarkerDialog
          marker={selectedMarkerForEdit || undefined}
          checkpointId={checkpoint.id}
          onClose={() => {
            setShowMarkerDialog(false);
            setSelectedMarkerForEdit(null);
          }}
          onSave={handleMarkerSave}
          onDelete={() => {
            setMarkers(markers.filter((m) => m.id !== selectedMarkerForEdit?.id));
            setShowMarkerDialog(false);
            setSelectedMarkerForEdit(null);
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// Marker Row 组件
// ============================================================================

interface MarkerRowProps {
  marker: CheckpointMarker;
  checkpointId: string;
  onDelete: () => void;
  onEdit: () => void;
  isReadOnly?: boolean;
}

function MarkerRow({
  marker,
  checkpointId,
  onDelete,
  onEdit,
  isReadOnly = false,
}: MarkerRowProps) {
  // 图标映射
  const iconMap: { [key: string]: React.ComponentType<any> } = {
    Clock,
    Zap,
    Bug,
    Lightbulb,
    CheckCircle2,
    MessageSquare,
    AlertCircle,
  };

  const IconComponent = iconMap[marker.emoji] || Clock;

  return (
    <div className={`flex items-center justify-between p-2 rounded text-sm group transition ${
      marker.is_completed
        ? 'bg-green-50 hover:bg-green-100'
        : 'bg-gray-50 hover:bg-gray-100'
    }`}>
      <div className="flex items-center gap-2 flex-1">
        <div className="relative">
          <IconComponent className={`w-5 h-5 ${
            marker.is_completed ? 'text-green-600' : 'text-blue-600'
          }`} />
          {marker.is_completed && (
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-600 rounded-full flex items-center justify-center">
              <span className="text-white text-xs">✓</span>
            </div>
          )}
        </div>
        <div className="flex-1">
          <p className={`font-medium ${marker.is_completed ? 'line-through text-gray-500' : ''}`}>
            {marker.title}
          </p>
          {marker.description && (
            <p className="text-xs text-gray-600">{marker.description}</p>
          )}
          <p className="text-xs text-gray-500">
            ⏱️ {formatDuration(marker.duration_seconds)}
          </p>
        </div>
      </div>

      {!isReadOnly && (
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition">
          <button
            onClick={onEdit}
            className="p-1 text-blue-500 hover:bg-blue-100 rounded"
          >
            <Edit2 className="w-3 h-3" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-red-500 hover:bg-red-100 rounded"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 新建 Checkpoint 对话框
// ============================================================================

interface NewCheckpointDialogProps {
  onClose: () => void;
  onSave: () => void;
  title: string;
  onTitleChange: (title: string) => void;
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  isLoading: boolean;
}

function NewCheckpointDialog({
  onClose,
  onSave,
  title,
  onTitleChange,
  selectedTags,
  onTagsChange,
  isLoading,
}: NewCheckpointDialogProps) {
  const { tags: allTags } = useOrbitTags();

  const toggleTag = (tagId: string) => {
    onTagsChange(
      selectedTags.includes(tagId)
        ? selectedTags.filter((t) => t !== tagId)
        : [...selectedTags, tagId]
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <h2 className="text-lg font-semibold mb-4">新建检查点</h2>

        {/* 标题输入 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            标题 *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="Enter checkpoint title:"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            autoFocus
          />
        </div>

        {/* 标签选择 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            标签
          </label>
          <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
            {allTags.map((tag) => (
              <button
                key={tag.id}
                onClick={() => onTagsChange(selectedTags.includes(tag.id) ? selectedTags.filter(t => t !== tag.id) : [...selectedTags, tag.id])}
                className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1 transition ${
                  selectedTags.includes(tag.id)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: tag.color }}
                />
                {tag.name}
              </button>
            ))}
          </div>
        </div>

        {/* 按钮 */}
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            取消
          </button>
          <button
            onClick={onSave}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition"
          >
            确定
          </button>
        </div>
      </div>
    </div>
  );
}
