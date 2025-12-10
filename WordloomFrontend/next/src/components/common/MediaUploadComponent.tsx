'use client';

/**
 * 统一媒体上传组件
 * 支持上传、删除、预览任何实体类型的媒体
 */

import React, { useRef, useState } from 'react';
import { Trash2, ImagePlus, Download } from 'lucide-react';
import {
  uploadMedia,
  deleteMedia,
  MediaEntityType,
  MediaResource,
} from '@/modules/orbit/domain/media';

export interface MediaUploadComponentProps {
  /** 工作区 ID */
  workspaceId: string;
  /** 媒体实体类型 */
  entityType: MediaEntityType;
  /** 实体 ID */
  entityId: string;
  /** 现有媒体列表 */
  media: MediaResource[];
  /** 当媒体列表更新时调用 */
  onMediaUpdate: (media: MediaResource[]) => void;
  /** 单行最多显示多少张缩略图（默认 5）*/
  thumbsPerRow?: number;
  /** 缩略图大小（默认 120）*/
  thumbSize?: number;
  /** 最多允许上传多少张图片（默认 5）*/
  maxImages?: number;
  /** 是否显示下载按钮（默认 false）*/
  showDownload?: boolean;
  /** 自定义样式类名 */
  className?: string;
}

export function MediaUploadComponent({
  workspaceId,
  entityType,
  entityId,
  media,
  onMediaUpdate,
  thumbsPerRow = 5,
  thumbSize = 120,
  maxImages = 5,
  showDownload = false,
  className = '',
}: MediaUploadComponentProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.currentTarget.files?.[0];
    if (!file) return;

    if (media.length >= maxImages) {
      setError(`最多只能上传 ${maxImages} 张图片`);
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const newMedia = await uploadMedia(
        file,
        workspaceId,
        entityType,
        entityId,
        media.length
      );

      onMediaUpdate([...media, newMedia]);

      // 重置 input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (mediaId: string, index: number) => {
    if (!confirm('确定要删除这张图片吗？')) return;

    try {
      await deleteMedia(mediaId);
      onMediaUpdate(media.filter((_, i) => i !== index));
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    }
  };

  const handleDownload = (mediaResource: MediaResource) => {
    const link = document.createElement('a');
    link.href = mediaResource.file_path;
    link.download = mediaResource.file_name;
    link.click();
  };

  return (
    <div className={`space-y-2 ${className}`}>
      {/* 错误提示 */}
      {error && (
        <div className="text-sm text-red-600 bg-red-50 px-2 py-1 rounded">
          {error}
        </div>
      )}

      {/* 媒体网格 */}
      {media.length > 0 && (
        <div
          className="flex gap-2 flex-wrap"
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(auto-fill, minmax(${thumbSize}px, 1fr))`,
          }}
        >
          {media.map((m, idx) => (
            <div
              key={m.id}
              className="relative group bg-gray-100 rounded border border-gray-300 overflow-hidden"
              style={{ width: `${thumbSize}px`, height: `${thumbSize}px` }}
            >
              <img
                src={m.file_path}
                alt={`${idx + 1}`}
                className="w-full h-full object-cover"
              />

              {/* 操作按钮 - hover 显示 */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-1">
                {showDownload && (
                  <button
                    onClick={() => handleDownload(m)}
                    className="p-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                    title="下载"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => handleDelete(m.id, idx)}
                  className="p-1 bg-red-500 text-white rounded hover:bg-red-600"
                  title="删除"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* 序号标签 */}
              <div className="absolute bottom-1 left-1 text-xs text-white bg-black/70 px-1 rounded">
                {idx + 1}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 上传按钮 */}
      {media.length < maxImages && (
        <div>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm rounded transition"
          >
            <ImagePlus className="w-4 h-4" />
            {uploading ? '上传中...' : '添加图片'}
            {media.length > 0 && ` (${media.length}/${maxImages})`}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            disabled={uploading}
            hidden
          />
        </div>
      )}

      {/* 已达最大数量提示 */}
      {media.length >= maxImages && (
        <div className="text-xs text-gray-600">
          已达到最大上传数量 ({maxImages})
        </div>
      )}
    </div>
  );
}
