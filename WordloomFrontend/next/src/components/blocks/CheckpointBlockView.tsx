'use client';

import React, { useEffect, useState, useRef } from 'react';
import Image from 'next/image';
import { Trash2, Clock, X, Upload, ImagePlus, ChevronLeft, ChevronRight } from 'lucide-react';
import { Block, CheckpointBlock } from '@/modules/orbit/domain/blocks';
import {
  getCheckpoint,
  createCheckpointMarker,
  updateCheckpointMarker,
  deleteCheckpointMarker,
  updateCheckpoint,
  formatDuration
} from '@/modules/orbit/domain/checkpoints';
import type { CheckpointDetail, CheckpointMarker, CreateCheckpointMarkerRequest } from '@/modules/orbit/domain/checkpoints';
import { uploadMedia, getMediaByEntity, deleteMedia, MediaEntityType, MediaResource } from '@/modules/orbit/domain/media';
import { FloatingSaveBar } from '@/components/FloatingSaveBar';

interface CheckpointBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
  noteId?: string;
  onSave?: () => Promise<void>; // 保存回调，用于 Ctrl+S 和浮动保存栏
}

export function CheckpointBlockView({
  block,
  onUpdate,
  noteId,
  onSave,
}: CheckpointBlockViewProps) {
  const checkpoint = block as CheckpointBlock;
  const checkpointId = checkpoint.content.checkpointId;

  // 调试：打印收到的 IDs
  console.log('[CHECKPOINT_VIEW] Received:', {
    noteId,
    checkpointId,
    blockId: block.id,
  });

  const [checkpointData, setCheckpointData] = useState<CheckpointDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingTitle, setEditingTitle] = useState(false);
  const [editingCreatedAt, setEditingCreatedAt] = useState(false);
  const [checkpointTitle, setCheckpointTitle] = useState('');
  const [checkpointCreatedAt, setCheckpointCreatedAt] = useState('');

  const [isAddingMarker, setIsAddingMarker] = useState(false);
  const [markerTitle, setMarkerTitle] = useState('');
  const [markerDescription, setMarkerDescription] = useState('');
  const [markerStartTime, setMarkerStartTime] = useState('');
  const [markerEndTime, setMarkerEndTime] = useState('');
  const [isSubmittingMarker, setIsSubmittingMarker] = useState(false);

  const [editingMarkerIds, setEditingMarkerIds] = useState<Set<string>>(new Set());
  const [markerEditData, setMarkerEditData] = useState<Record<string, Partial<CheckpointMarker>>>({});
  const [markerTimeEditIds, setMarkerTimeEditIds] = useState<Set<string>>(new Set());

  // 图片上传相关状态
  const [uploadingMarkerId, setUploadingMarkerId] = useState<string | null>(null);
  const markerImageFileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const [markerMediaResources, setMarkerMediaResources] = useState<Record<string, MediaResource[]>>({});

  // Toast 提示
  const [toastMessage, setToastMessage] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // 图片调整大小相关状态
  const [resizingMarkerId, setResizingMarkerId] = useState<string | null>(null);
  const [resizeStartX, setResizeStartX] = useState(0);
  const [resizeStartWidth, setResizeStartWidth] = useState(0);

  // Lightbox 放大图片状态
  const [enlargedImageMarkerId, setEnlargedImageMarkerId] = useState<string | null>(null);

  // 文本框自动高度调整
  const markerTextareaRefs = useRef<Record<string, HTMLTextAreaElement | null>>({});

  const autoResizeTextarea = (markerId: string) => {
    const textarea = markerTextareaRefs.current[markerId];
    if (textarea) {
      textarea.style.height = 'auto';
      const scrollHeight = textarea.scrollHeight;
      // 每行高度约为 20px (根据 text-sm 和 leading-relaxed)
      const lineHeight = 20;
      const lines = Math.ceil(scrollHeight / lineHeight);
      // 限制最多 25 行，超过 25 行显示滚动条
      if (lines > 25) {
        textarea.style.height = (25 * lineHeight) + 'px';
        textarea.style.overflowY = 'auto';
      } else {
        textarea.style.height = scrollHeight + 'px';
        textarea.style.overflowY = 'hidden';
      }
    }
  };

  // Lightbox 辅助函数
  const getMarkerImages = () => {
    // 从新的媒体资源系统获取图片
    const markersWithImages: { markerId: string; images: { url: string; index: number }[] }[] = [];
    checkpointData?.markers.forEach(m => {
      const media = markerMediaResources[m.id];
      if (media && media.length > 0) {
        markersWithImages.push({
          markerId: m.id,
          images: media.map((img, idx) => ({ url: img.file_path, index: idx }))
        });
      }
    });
    return markersWithImages;
  };

  const getCurrentImageMarkerId = () => {
    return enlargedImageMarkerId?.split('_')[0]; // 格式：markerId_imageIndex
  };

  const getCurrentImageIndex = () => {
    if (!enlargedImageMarkerId) return -1;
    const [markerId, indexStr] = enlargedImageMarkerId.split('_');
    return parseInt(indexStr, 10);
  };

  const goToPrevImage = () => {
    if (!enlargedImageMarkerId) return;
    const [markerId, indexStr] = enlargedImageMarkerId.split('_');
    const currentIndex = parseInt(indexStr, 10);
    const media = markerMediaResources[markerId];

    if (media && currentIndex > 0) {
      setEnlargedImageMarkerId(`${markerId}_${currentIndex - 1}`);
    }
  };

  const goToNextImage = () => {
    if (!enlargedImageMarkerId) return;
    const [markerId, indexStr] = enlargedImageMarkerId.split('_');
    const currentIndex = parseInt(indexStr, 10);
    const media = markerMediaResources[markerId];

    if (media && currentIndex < media.length - 1) {
      setEnlargedImageMarkerId(`${markerId}_${currentIndex + 1}`);
    }
  };

  // ESC 键关闭 Lightbox，左右箭头键切换图片
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!enlargedImageMarkerId) return;

      switch (e.key) {
        case 'Escape':
          e.preventDefault();
          setEnlargedImageMarkerId(null);
          break;
        case 'ArrowLeft':
          e.preventDefault();
          goToPrevImage();
          break;
        case 'ArrowRight':
          e.preventDefault();
          goToNextImage();
          break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [enlargedImageMarkerId]);

  // Toast 自动消失效果
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => {
        setToastMessage(null);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  const getCurrentTimeFormatted = (): string => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  };

  const formatTimeForDisplay = (isoString: string): string => {
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  };

  const parseTimeFromInput = (input: string): string | null => {
    try {
      // 去除首尾空格
      const trimmed = input.trim();
      const [dateStr, timeStr] = trimmed.split(' ');
      if (!dateStr || !timeStr) return null;
      const [year, month, day] = dateStr.split('-').map(Number);
      const timeParts = timeStr.split(':').map(Number);
      const hours = timeParts[0];
      const minutes = timeParts[1];
      const seconds = timeParts[2] || 0;
      const date = new Date(year, month - 1, day, hours, minutes, seconds);
      if (isNaN(date.getTime())) return null;
      return date.toISOString();
    } catch {
      return null;
    }
  };

  useEffect(() => {
    const loadCheckpoint = async () => {
      if (!checkpointId) {
        setError('Missing checkpoint ID');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await getCheckpoint(checkpointId);
        setCheckpointData(data);
        setCheckpointTitle(data.title || 'Untitled Checkpoint');
        setCheckpointCreatedAt(formatTimeForDisplay(data.created_at));

        // 加载所有 marker 的媒体资源
        const mediaResourcesMap: Record<string, MediaResource[]> = {};
        for (const marker of data.markers) {
          try {
            const media = await getMediaByEntity(
              MediaEntityType.CHECKPOINT_MARKER,
              marker.id
            );
            mediaResourcesMap[marker.id] = media;
          } catch (err) {
            console.warn(`Failed to load media for marker ${marker.id}:`, err);
            mediaResourcesMap[marker.id] = [];
          }
        }
        setMarkerMediaResources(mediaResourcesMap);

        setError(null);
      } catch (err) {
        console.error('Failed to load checkpoint:', err);
        setError(err instanceof Error ? err.message : 'Failed to load checkpoint');
      } finally {
        setLoading(false);
      }
    };

    loadCheckpoint();
  }, [checkpointId]);

  // 当 checkpointData 加载完毕时，自动调整所有 textarea 的高度
  useEffect(() => {
    if (checkpointData?.markers) {
      // 使用 setTimeout 确保 DOM 已渲染
      setTimeout(() => {
        checkpointData.markers.forEach(marker => {
          autoResizeTextarea(marker.id);
        });
      }, 100);
    }
  }, [checkpointData?.markers, markerMediaResources]);

  // 添加全局 Ctrl+S 快捷键支持 - 调用 onSave 回调
  useEffect(() => {
    if (!onSave) return; // 如果没有 onSave，不添加监听

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S (Windows/Linux) 或 Cmd+S (Mac)
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        console.log('[CheckpointBlockView] Ctrl+S 被按下，调用 onSave');
        onSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSave]);

  const calculateTimeDifference = (startTime: string, endTime: string): string => {
    try {
      const start = new Date(startTime);
      const end = new Date(endTime);
      const diffSeconds = Math.floor((end.getTime() - start.getTime()) / 1000);
      if (diffSeconds < 0) return '0s';
      return formatDuration(diffSeconds);
    } catch {
      return 'Error';
    }
  };

  const calculateTotalTime = (): string => {
    if (!checkpointData?.markers || checkpointData.markers.length === 0) {
      return 'No data';
    }
    const firstMarker = checkpointData.markers[0];
    const lastMarker = checkpointData.markers[checkpointData.markers.length - 1];
    return calculateTimeDifference(firstMarker.started_at, lastMarker.ended_at);
  };

  const handleSaveTitle = async () => {
    if (!checkpointTitle.trim()) {
      alert('Title cannot be empty');
      return;
    }
    try {
      await updateCheckpoint(checkpointId, { title: checkpointTitle });
      setCheckpointData(prev => prev ? { ...prev, title: checkpointTitle } : null);
      setEditingTitle(false);
    } catch (err) {
      console.error('Failed to save title:', err);
      alert(`Failed to save: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleSaveCreatedAt = async () => {
    const newCreatedAt = parseTimeFromInput(checkpointCreatedAt);
    if (!newCreatedAt) {
      alert('Invalid time format. Use YYYY-MM-DD HH:MM');
      return;
    }
    setCheckpointData(prev => prev ? { ...prev, created_at: newCreatedAt } : null);
    setEditingCreatedAt(false);
  };

  const handleAddMarker = async () => {
    const startTime = getCurrentTimeFormatted();
    const endTime = getCurrentTimeFormatted();
    const startIso = parseTimeFromInput(startTime);
    const endIso = parseTimeFromInput(endTime);

    if (!startIso || !endIso) {
      alert('Failed to generate time');
      return;
    }

    try {
      setIsSubmittingMarker(true);
      const request: CreateCheckpointMarkerRequest = {
        title: 'Untitled',
        description: '',
        started_at: startIso,
        ended_at: endIso,
        is_completed: true,
      };

      await createCheckpointMarker(checkpointId, request);
      const updatedData = await getCheckpoint(checkpointId);
      setCheckpointData(updatedData);
      setToastMessage({ message: 'Marker 创建成功！', type: 'success' });

      setIsAddingMarker(false);
    } catch (err) {
      console.error('Failed to add marker:', err);
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setToastMessage({ message: `创建失败: ${errorMsg}`, type: 'error' });
    } finally {
      setIsSubmittingMarker(false);
    }
  };

  const handleSaveMarkerEdit = async (marker: CheckpointMarker) => {
    const editData = markerEditData[marker.id];
    if (!editData) return;

    try {
      await updateCheckpointMarker(checkpointId, marker.id, editData);
      const updatedData = await getCheckpoint(checkpointId);
      setCheckpointData(updatedData);

      setEditingMarkerIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(marker.id);
        return newSet;
      });

      setMarkerEditData(prev => {
        const newData = { ...prev };
        delete newData[marker.id];
        return newData;
      });
    } catch (err) {
      console.error('Failed to update marker:', err);
      alert(`Failed to update: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleDeleteMarker = async (markerId: string) => {
    if (!confirm('Are you sure?')) return;

    try {
      await deleteCheckpointMarker(checkpointId, markerId);
      const updatedData = await getCheckpoint(checkpointId);
      setCheckpointData(updatedData);
    } catch (err) {
      console.error('Failed to delete marker:', err);
      alert(`Failed to delete: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // 上传 marker 图片（使用统一媒体系统）
  const handleUploadMarkerImage = async (markerId: string, file: File) => {
    if (!file) return;

    try {
      setUploadingMarkerId(markerId);

      // 获取当前 marker
      const marker = checkpointData?.markers.find(m => m.id === markerId);
      if (!marker) return;

      // 检查图片数量是否已达到最大值
      const currentImageCount = markerMediaResources[markerId]?.length || 0;
      if (currentImageCount >= 5) {
        alert('最多只能添加 5 张图片');
        setUploadingMarkerId(null);
        return;
      }

      console.log('[UPLOAD] Starting marker image upload', {
        markerId,
        fileName: file.name,
        currentImageCount,
      });

      // 使用新的统一媒体 API 上传
      // 需要 workspace_id，暂时使用 noteId 作为 workspace_id
      const workspaceId = noteId || 'unknown';
      const mediaResource = await uploadMedia(
        file,
        workspaceId,
        MediaEntityType.CHECKPOINT_MARKER,
        markerId,
        currentImageCount
      );

      console.log('[UPLOAD] Upload successful:', mediaResource);

      // 更新本地媒体资源列表
      setMarkerMediaResources(prev => ({
        ...prev,
        [markerId]: [...(prev[markerId] || []), mediaResource]
      }));

      // 更新 marker 的 image_urls（保持兼容性）
      const newImageUrls = [...(marker.image_urls || []), { url: mediaResource.file_path }];
      await updateCheckpointMarker(checkpointId, markerId, {
        image_urls: newImageUrls,
      });

      // 更新本地状态
      if (checkpointData) {
        const newMarkers = checkpointData.markers.map(m =>
          m.id === markerId ? { ...m, image_urls: newImageUrls } : m
        );
        setCheckpointData({ ...checkpointData, markers: newMarkers });
      }

      setUploadingMarkerId(null);
    } catch (err) {
      console.error('Failed to upload image:', err);
      alert(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setUploadingMarkerId(null);
    }
  };

  // 删除 marker 的单张图片（使用统一媒体系统）
  const handleDeleteMarkerImage = async (markerId: string, imageIndex: number) => {
    if (!confirm('Delete this image?')) return;

    try {
      const marker = checkpointData?.markers.find(m => m.id === markerId);
      if (!marker || !marker.image_urls) return;

      // 从列表中移除该索引的图片
      const newImageUrls = marker.image_urls.filter((_, idx) => idx !== imageIndex);

      // 如果有媒体资源，删除对应的资源
      const mediaResources = markerMediaResources[markerId];
      if (mediaResources && mediaResources[imageIndex]) {
        const mediaResource = mediaResources[imageIndex];
        try {
          await deleteMedia(mediaResource.id);
        } catch (err) {
          console.error('Failed to delete media resource:', err);
          // 继续删除，即使媒体资源删除失败
        }
      }

      // 更新后端
      await updateCheckpointMarker(checkpointId, markerId, {
        image_urls: newImageUrls,
      });

      // 更新本地状态
      if (checkpointData) {
        const newMarkers = checkpointData.markers.map(m =>
          m.id === markerId ? { ...m, image_urls: newImageUrls } : m
        );
        setCheckpointData({ ...checkpointData, markers: newMarkers });
      }

      // 更新媒体资源列表
      setMarkerMediaResources(prev => ({
        ...prev,
        [markerId]: (prev[markerId] || []).filter((_, idx) => idx !== imageIndex)
      }));

      console.log('[DELETE_IMAGE] ✓ Image deleted:', { markerId, imageIndex });
    } catch (err) {
      console.error('Failed to delete image:', err);
      alert(`Failed to delete image: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // 快速填充结束时间为当前时间
  const handleFillEndTimeNow = (marker: CheckpointMarker) => {
    const nowIso = new Date().toISOString();

    // 1. 更新本地编辑数据
    setMarkerEditData(prev => ({
      ...prev,
      [marker.id]: { ...(prev[marker.id] || marker), ended_at: nowIso }
    }));

    // 2. 确保该 marker 处于编辑状态
    setEditingMarkerIds(prev => new Set([...prev, marker.id]));

    // 3. 立即保存到数据库，但不重新加载（保留用户编辑内容）
    updateCheckpointMarker(checkpointId, marker.id, { ended_at: nowIso }).catch(err => {
      console.error('Failed to fill end time:', err);
    });
  };

  // handleSaveCheckpoint 已删除 - 现在使用全局浮动保存按钮

  // 全局保存函数 - 用于浮动保存栏调用
  const handleGlobalSave = async () => {
    try {
      console.log('[CheckpointBlockView] 开始全局保存...', {
        editingMarkerIds: Array.from(editingMarkerIds),
        checkpointTitle,
        checkpointCreatedAt,
      });

      // 1. 保存 Checkpoint 本身的改动（标题、创建时间）
      const checkpointUpdates: Record<string, any> = {};

      if (checkpointData && checkpointTitle !== checkpointData.title) {
        if (!checkpointTitle.trim()) {
          throw new Error('Title cannot be empty');
        }
        checkpointUpdates.title = checkpointTitle;
        console.log('[CheckpointBlockView] 准备保存标题:', checkpointTitle);
      }

      if (checkpointData && checkpointCreatedAt !== checkpointData.created_at) {
        const newCreatedAt = parseTimeFromInput(checkpointCreatedAt);
        if (!newCreatedAt) {
          throw new Error('Invalid time format. Use YYYY-MM-DD HH:MM');
        }
        checkpointUpdates.created_at = newCreatedAt;
        console.log('[CheckpointBlockView] 准备保存创建时间:', newCreatedAt);
      }

      if (Object.keys(checkpointUpdates).length > 0) {
        console.log('[CheckpointBlockView] 保存 Checkpoint 更新...');
        await updateCheckpoint(checkpointId, checkpointUpdates);
        console.log('[CheckpointBlockView] ✓ Checkpoint 更新成功');
      }

      // 2. 保存所有待编辑的 marker
      if (editingMarkerIds.size > 0) {
        console.log('[CheckpointBlockView] 保存 marker 编辑...', {
          count: editingMarkerIds.size,
          ids: Array.from(editingMarkerIds),
        });

        const markerSavePromises: Promise<any>[] = [];

        for (const markerId of editingMarkerIds) {
          const marker = checkpointData?.markers.find(m => m.id === markerId);
          if (marker) {
            const editData = markerEditData[markerId];
            if (editData) {
              console.log(`[CheckpointBlockView] 保存 marker ${markerId}:`, editData);
              markerSavePromises.push(
                updateCheckpointMarker(checkpointId, markerId, editData)
                  .then(() => console.log(`[CheckpointBlockView] ✓ Marker ${markerId} 保存成功`))
                  .catch(err => {
                    console.error(`[CheckpointBlockView] ✗ Marker ${markerId} 保存失败:`, err);
                    throw err;
                  })
              );
            }
          }
        }

        if (markerSavePromises.length > 0) {
          await Promise.all(markerSavePromises);
          console.log('[CheckpointBlockView] ✓ 所有 marker 保存成功');
        }
      }

      // 3. 刷新数据
      console.log('[CheckpointBlockView] 刷新数据...');
      const updated = await getCheckpoint(checkpointId);
      setCheckpointData(updated);

      // 更新状态以反映保存的值
      if (updated) {
        setCheckpointTitle(updated.title);
        setCheckpointCreatedAt(updated.created_at);
      }

      // 4. 清除编辑状态
      setEditingMarkerIds(new Set());
      setMarkerEditData({});
      setMarkerTimeEditIds(new Set());

      console.log('[CheckpointBlockView] ✓ 全局保存完成！');
    } catch (err) {
      console.error('[CheckpointBlockView] 保存失败:', err);
      throw err; // 让 FloatingSaveBar 处理错误
    }
  };

  if (loading) return <div className="p-4 text-gray-600">Loading...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!checkpointData) return <div className="p-4 text-gray-600">No data</div>;

  const isComplete = checkpointData.completion_percentage === 100;

  return (
    <div>
      <div className="p-3 bg-white border border-gray-300 rounded-lg space-y-2">
        {/* Header */}
        <div className="relative group pb-2 border-b border-gray-300">
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center gap-2 min-w-0">
              <input
                type="text"
                value={checkpointTitle}
                onChange={(e) => setCheckpointTitle(e.target.value)}
                onFocus={() => setEditingTitle(true)}
                onBlur={() => {
                  if (editingTitle && checkpointTitle.trim()) {
                    handleSaveTitle();
                  }
                }}
                className={`w-full text-base font-medium bg-transparent border-0 border-b min-w-0 ${
                  editingTitle
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-transparent hover:border-gray-400'
                } focus:outline-none focus:border-blue-600 px-1 py-0.5 text-gray-900`}
              />
            </div>

            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
              <div className="relative group/info">
                <button className="px-2 py-1 text-xs text-gray-600 hover:text-gray-900" title="Info">
                  ℹ️
                </button>

                <div className="absolute top-full right-0 mt-1 p-2 bg-gray-800 text-white text-xs rounded shadow-lg
                              opacity-0 group-hover/info:opacity-100 transition-opacity whitespace-nowrap z-20
                              pointer-events-none group-hover/info:pointer-events-auto">
                  <div>Completion: {Math.round(checkpointData.completion_percentage || 0)}%</div>
                  {isComplete && <div className="text-green-300">✓ Complete</div>}
                  <div className="text-gray-300 mt-1">Total: {calculateTotalTime()}</div>
                </div>
              </div>

              <button
                onClick={handleAddMarker}
                disabled={isSubmittingMarker}
                className="px-2 py-1 text-xs text-gray-600 hover:text-gray-900 disabled:opacity-50"
                title="Add Record"
              >
                ➕
              </button>
            </div>

            <span className="text-gray-600">|</span>
            <span className="text-sm font-semibold text-gray-800 whitespace-nowrap">
              ⏱️ Records ({checkpointData.markers?.length || 0})
            </span>
          </div>
        </div>

        {/* Markers */}

          {checkpointData.markers && checkpointData.markers.length > 0 ? (
            <div className="space-y-1.5">
              {checkpointData.markers.map((marker, index) => {
                const isEditing = editingMarkerIds.has(marker.id);
                const isTimeEditing = markerTimeEditIds.has(marker.id);
                const editData = markerEditData[marker.id] || marker;
                const prevMarker = index > 0 ? checkpointData.markers![index - 1] : null;
                const prevTime = prevMarker ? new Date(prevMarker.ended_at) : new Date(marker.started_at);
                const segmentGap = calculateTimeDifference(prevTime.toISOString(), marker.started_at);

                return (
                  <div
                    key={marker.id}
                    className="relative group border border-gray-300 rounded p-2 bg-gray-50 hover:bg-white hover:shadow-md hover:border-gray-400 transition"
                  >
                    {/* Hidden file input for marker images */}
                    <input
                      ref={(el) => {
                        if (el) {
                          markerImageFileInputRefs.current[marker.id] = el;
                        }
                      }}
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          handleUploadMarkerImage(marker.id, file);
                        }
                        // Reset this specific input
                        if (markerImageFileInputRefs.current[marker.id]) {
                          markerImageFileInputRefs.current[marker.id]!.value = '';
                        }
                      }}
                    />

                    {/* Content - 全文本布局 + 下方缩略图网格 */}
                    <div className="space-y-2 relative">
                      {/* 上传 + 删除按钮 - 右上角绝对定位 */}
                      <div className="absolute -top-8 right-0 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                        <button
                          onClick={() => markerImageFileInputRefs.current[marker.id]?.click()}
                          disabled={uploadingMarkerId === marker.id || (marker.image_urls?.length || 0) >= 5}
                          className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded transition disabled:opacity-50"
                          title={(marker.image_urls?.length || 0) >= 5 ? "已达到最大图片数量(5)" : "上传图片"}
                        >
                          <ImagePlus className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleDeleteMarker(marker.id)}
                          className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition"
                          title="删除 marker"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      {/* 文本内容 */}
                      <textarea
                        ref={(el) => {
                          if (el) markerTextareaRefs.current[marker.id] = el;
                        }}
                        value={editingMarkerIds.has(marker.id) ? (markerEditData[marker.id]?.title || '') : marker.title}
                        onChange={(e) => {
                          if (editingMarkerIds.has(marker.id)) {
                            setMarkerEditData(prev => ({
                              ...prev,
                              [marker.id]: { ...prev[marker.id], title: e.target.value }
                            }));
                          }
                          autoResizeTextarea(marker.id);
                        }}
                        onFocus={() => {
                          if (!editingMarkerIds.has(marker.id)) {
                            setEditingMarkerIds(prev => new Set([...prev, marker.id]));
                            setMarkerEditData(prev => ({
                              ...prev,
                              [marker.id]: { ...marker }
                            }));
                          }
                          setTimeout(() => autoResizeTextarea(marker.id), 0);
                        }}
                        onBlur={() => {
                          if (editingMarkerIds.has(marker.id)) {
                            handleSaveMarkerEdit(marker);
                          }
                        }}
                        className={`w-full px-1 py-0.5 text-sm bg-transparent border-0 border-b resize-none focus:outline-none leading-relaxed ${
                          editingMarkerIds.has(marker.id)
                            ? 'border-blue-400 bg-blue-50'
                            : 'border-transparent hover:border-gray-300'
                        }`}
                        placeholder="Enter content..."
                      />

                      {/* 时间信息 - 紧凑显示 */}
                      <div className="flex items-center gap-1 flex-wrap text-xs text-gray-600">
                        <input
                          type="text"
                          value={editingMarkerIds.has(marker.id) ? (markerEditData[marker.id]?.started_at ? formatTimeForDisplay(markerEditData[marker.id].started_at!) : formatTimeForDisplay(marker.started_at)) : formatTimeForDisplay(marker.started_at)}
                          onChange={(e) => {
                            if (editingMarkerIds.has(marker.id)) {
                              const iso = parseTimeFromInput(e.target.value);
                              if (iso) {
                                setMarkerEditData(prev => ({
                                  ...prev,
                                  [marker.id]: { ...prev[marker.id], started_at: iso }
                                }));
                              }
                            }
                          }}
                          onFocus={() => {
                            if (!editingMarkerIds.has(marker.id)) {
                              setEditingMarkerIds(prev => new Set([...prev, marker.id]));
                              setMarkerEditData(prev => ({
                                ...prev,
                                [marker.id]: { ...marker }
                              }));
                            }
                          }}
                          onBlur={() => {
                            if (editingMarkerIds.has(marker.id)) {
                              handleSaveMarkerEdit(marker);
                            }
                          }}
                          className="px-0.5 py-0 text-xs bg-transparent border-0 border-b border-transparent hover:border-gray-300 focus:outline-none focus:border-blue-600 font-medium"
                        />
                        <span className="text-gray-700 font-semibold">→</span>
                        <input
                          type="text"
                          value={editingMarkerIds.has(marker.id) ? (markerEditData[marker.id]?.ended_at ? formatTimeForDisplay(markerEditData[marker.id].ended_at!) : formatTimeForDisplay(marker.ended_at)) : formatTimeForDisplay(marker.ended_at)}
                          onChange={(e) => {
                            if (editingMarkerIds.has(marker.id)) {
                              const iso = parseTimeFromInput(e.target.value);
                              if (iso) {
                                setMarkerEditData(prev => ({
                                  ...prev,
                                  [marker.id]: { ...prev[marker.id], ended_at: iso }
                                }));
                              }
                            }
                          }}
                          onFocus={() => {
                            if (!editingMarkerIds.has(marker.id)) {
                              setEditingMarkerIds(prev => new Set([...prev, marker.id]));
                              setMarkerEditData(prev => ({
                                ...prev,
                                [marker.id]: { ...marker }
                              }));
                            }
                          }}
                          onBlur={() => {
                            if (editingMarkerIds.has(marker.id)) {
                              handleSaveMarkerEdit(marker);
                            }
                          }}
                          className="px-0.5 py-0 text-xs bg-transparent border-0 border-b border-transparent hover:border-gray-300 focus:outline-none focus:border-blue-600 font-medium"
                        />
                        {/* 快速填充当前时间按钮 */}
                        <button
                          onClick={() => handleFillEndTimeNow(marker)}
                          className="p-0.5 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded transition flex-shrink-0"
                          title="填充为当前时间"
                        >
                          <Clock className="w-3 h-3" />
                        </button>
                        <span className="text-gray-500">({calculateTimeDifference(marker.started_at, marker.ended_at)})</span>
                        {segmentGap !== '0s' && (
                          <span className="text-gray-500">(+{segmentGap})</span>
                        )}
                      </div>

                      {/* 缩略图网格 - 下方显示，最多 5 张，每张 120x120 */}
                      {markerMediaResources[marker.id] && markerMediaResources[marker.id].length > 0 && (
                        <div className="flex gap-2 flex-wrap mt-2 pt-2 border-t border-gray-200">
                          {markerMediaResources[marker.id].map((media, imgIdx) => {
                            const imageUrl = media.file_path.startsWith('http')
                              ? media.file_path
                              : `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}${media.file_path}`;
                            return (
                            <div
                              key={`${marker.id}-${imgIdx}`}
                              className="relative group/thumb bg-gray-100 rounded border border-gray-300 overflow-hidden flex-shrink-0"
                              style={{ width: '120px', height: '120px', position: 'relative' }}
                            >
                              <Image
                                src={imageUrl}
                                alt={`Image ${imgIdx + 1}`}
                                fill
                                sizes="120px"
                                quality={90}
                                priority={imgIdx === 0}
                                onClick={() => setEnlargedImageMarkerId(`${marker.id}_${imgIdx}`)}
                                className="object-contain cursor-pointer hover:opacity-80 transition"
                                title={`点击查看大图 (${imgIdx + 1}/${markerMediaResources[marker.id].length})`}
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                              {/* 删除按钮 - 右上角，hover 时显示 */}
                              <button
                                onClick={() => handleDeleteMarkerImage(marker.id, imgIdx)}
                                className="absolute top-0 right-0 p-0.5 bg-red-500 text-white rounded transition opacity-0 group-hover/thumb:opacity-100 z-10"
                                title="删除此图片"
                              >
                                <X className="w-3 h-3" />
                              </button>
                              {/* 图片编号 - 左下角 */}
                              <div className="absolute bottom-0 left-0 px-1 py-0 text-xs text-white bg-black/50 z-10">
                                {imgIdx + 1}
                              </div>
                            </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-xs text-gray-500 italic">No records</div>
          )}

        {/* Lightbox Modal - 放大图片查看 */}
        {enlargedImageMarkerId && checkpointData?.markers && (
          <div
            className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
            onClick={() => setEnlargedImageMarkerId(null)}
          >
            <div
              className="relative flex items-center justify-center gap-4"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 上一张按钮 - 图片外左侧 */}
              {(() => {
                const currentIndex = getCurrentImageIndex();
                const [markerId] = enlargedImageMarkerId.split('_');
                const media = markerMediaResources[markerId];
                const totalImages = media?.length || 0;
                return totalImages > 1 && currentIndex > 0 ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      goToPrevImage();
                    }}
                    className="text-white hover:bg-white/20 rounded-full p-3 transition hover:scale-110 flex-shrink-0"
                    title="上一张 (← Arrow)"
                  >
                    <ChevronLeft className="w-8 h-8" />
                  </button>
                ) : <div className="w-14 flex-shrink-0" />;
              })()}

              {/* 图片容器 */}
              <div className="relative max-w-4xl max-h-screen flex items-center justify-center">
                {/* 主图片 */}
                {(() => {
                  const [markerId, indexStr] = enlargedImageMarkerId.split('_');
                  const imageIndex = parseInt(indexStr, 10);
                  const media = markerMediaResources[markerId];
                  const imagePath = media?.[imageIndex]?.file_path;
                  const imageUrl = imagePath?.startsWith('http')
                    ? imagePath
                    : `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}${imagePath}`;
                  return (
                    <img
                      src={imageUrl}
                      alt="Enlarged"
                      className="max-w-full max-h-screen object-contain"
                    />
                  );
                })()}

                {/* 关闭按钮 - 右上角 */}
                <button
                  onClick={() => setEnlargedImageMarkerId(null)}
                  className="absolute -top-10 -right-10 text-white hover:bg-white/20 rounded-full p-2 transition"
                  title="关闭 (ESC)"
                >
                  <X className="w-6 h-6" />
                </button>

                {/* 图片信息 - 左下角 */}
                {(() => {
                  const [markerId, indexStr] = enlargedImageMarkerId.split('_');
                  const imageIndex = parseInt(indexStr, 10);
                  const media = markerMediaResources[markerId];
                  return (
                    <div className="absolute bottom-4 left-4 text-white text-sm opacity-75 space-y-1">
                      <div>{imageIndex + 1} / {media?.length || 0}</div>
                    </div>
                  );
                })()}
              </div>

              {/* 下一张按钮 - 图片外右侧 */}
              {(() => {
                const [markerId] = enlargedImageMarkerId.split('_');
                const media = markerMediaResources[markerId];
                const currentIndex = getCurrentImageIndex();
                const totalImages = media?.length || 0;
                return totalImages > 1 && currentIndex < totalImages - 1 ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      goToNextImage();
                    }}
                    className="text-white hover:bg-white/20 rounded-full p-3 transition hover:scale-110 flex-shrink-0"
                    title="下一张 (→ Arrow)"
                  >
                    <ChevronRight className="w-8 h-8" />
                  </button>
                ) : <div className="w-14 flex-shrink-0" />;
              })()}
            </div>
          </div>
        )}
      </div>

      {/* 浮动保存栏 */}
      <FloatingSaveBar
        onSave={onSave || handleGlobalSave}
      />

      {/* Toast 通知 */}
      {toastMessage && (
        <div className={`fixed top-4 right-4 px-4 py-3 rounded-lg text-white text-sm font-medium shadow-lg z-50 animate-in fade-in slide-in-from-right-4 duration-200 ${
          toastMessage.type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`}>
          <div className="flex items-center gap-2">
            {toastMessage.type === 'success' ? (
              <span>✓</span>
            ) : (
              <span>✕</span>
            )}
            {toastMessage.message}
          </div>
        </div>
      )}
    </div>
  );
}
