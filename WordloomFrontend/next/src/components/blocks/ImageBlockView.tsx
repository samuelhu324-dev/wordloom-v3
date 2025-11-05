/**
 * ImageBlockView - 图片块视图（始终编辑状态）
 * 设计灵感：Notion、Figma、Medium
 * 布局：左图右文 + 美化预览
 */
'use client';

import React, { useState, useRef } from 'react';
import { Block, ImageBlock } from '@/modules/orbit/domain/blocks';
import { uploadImage } from '@/modules/orbit/domain/api';
import { AlertCircle, Check, Upload, RefreshCw } from 'lucide-react';

interface ImageBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
  noteId?: string;
}

interface ImageInfo {
  width?: number;
  height?: number;
  displayWidth?: number;
  displayHeight?: number;
  size?: string;
}

export function ImageBlockView({
  block,
  onUpdate,
  noteId,
}: ImageBlockViewProps) {
  const image = block as ImageBlock;
  const [url, setUrl] = useState(image.content.url || '');
  // 合并 description、alt、caption 为一个字段（向后兼容）
  const [description, setDescription] = useState(
    image.content.description || image.content.alt || image.content.caption || ''
  );
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [imageInfo, setImageInfo] = useState<ImageInfo>({});
  // 从 block 中读取已保存的宽度，如果没有则默认 400
  const [displayWidth, setDisplayWidth] = useState((image.content as any).displayWidth || 400);
  const [isResizing, setIsResizing] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isReplacing, setIsReplacing] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const resizeRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const saveToastRef = useRef<NodeJS.Timeout | null>(null);

  const handleSave = (widthToSave?: number | React.FocusEvent<HTMLTextAreaElement>) => {
    // 处理两种调用方式：直接传数字，或者从 onBlur 传事件
    const width = typeof widthToSave === 'number' ? widthToSave : displayWidth;
    console.log('[ImageBlockView] 保存图片块:', { url, description, displayWidth: width });
    onUpdate({
      ...block,
      content: {
        ...image.content,
        url,
        description,
        displayWidth: width,  // 保存宽度到 block content
      },
      updatedAt: new Date().toISOString(),
    });
  };

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    console.log('[ImageBlockView] 图片加载成功:', url);
    setImageLoaded(true);
    setImageError(false);

    // 获取图片尺寸信息
    setImageInfo({
      width: img.naturalWidth,
      height: img.naturalHeight,
    });
  };

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    console.error('[ImageBlockView] 图片加载失败:', url);
    setImageLoaded(false);
    setImageError(true);
  };

  const formatDimensions = () => {
    if (imageInfo.width && imageInfo.height) {
      return `${imageInfo.width} × ${imageInfo.height}`;
    }
    return null;
  };

  // 处理resize
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsResizing(true);
    const startX = e.clientX;
    const startWidth = displayWidth;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const newWidth = Math.max(200, startWidth + deltaX);
      setDisplayWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      handleSave();
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // 双击恢复原始尺寸
  const handleDoubleClick = () => {
    setDisplayWidth(400);
  };

  // 保存当前宽度到持久化存储
  const handleSaveWidth = () => {
    handleSave(displayWidth);

    // 显示成功提示
    setSaveSuccess(true);
    if (saveToastRef.current) clearTimeout(saveToastRef.current);
    saveToastRef.current = setTimeout(() => {
      setSaveSuccess(false);
    }, 2000);  // 2秒后消失
  };

  // 替换图片处理
  const handleReplaceClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.currentTarget.files?.[0];
    if (!file) return;

    if (!noteId) {
      alert('无法获取笔记 ID，请先保存笔记');
      return;
    }

    setIsReplacing(true);
    try {
      console.log('[ImageBlockView] 开始替换图片:', file.name);

      // 上传新图片
      const response = await uploadImage(file, noteId);

      // 更新 URL
      setUrl(response.url);
      setImageLoaded(false);
      setImageError(false);

      console.log('[ImageBlockView] 图片替换成功:', response.url);

      // 立即更新 block（无延迟）- 确保后端清理机制不会删除这个图片
      const updatedBlock = {
        ...block,
        content: {
          ...image.content,
          url: response.url,
          description,
          displayWidth: displayWidth,
        },
        updatedAt: new Date().toISOString(),
      };

      onUpdate(updatedBlock);

      // 显示成功提示
      setSaveSuccess(true);
      if (saveToastRef.current) clearTimeout(saveToastRef.current);
      saveToastRef.current = setTimeout(() => {
        setSaveSuccess(false);
      }, 2000);
    } catch (err) {
      console.error('[ImageBlockView] 替换图片失败:', err);
      alert('替换图片失败，请重试');
    } finally {
      setIsReplacing(false);
      // 重置文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // 恢复到保存的宽度
  const handleResetWidth = () => {
    setDisplayWidth(400);
  };

  return (
    <div className="space-y-4">
      {/* 主体：左图右文布局（整体可伸缩） */}
      {url ? (
        <div className="flex gap-4 bg-gradient-to-br from-blue-50 to-blue-25 rounded-xl p-4 border border-blue-100 hover:border-blue-300 transition-all duration-200 hover:shadow-lg" style={{ cursor: isResizing ? 'col-resize' : 'default' }}>

          {/* 左侧：图片预览（可调整大小） */}
          <div style={{ width: `${displayWidth}px`, flexShrink: 0 }}>
            <div className="relative rounded-lg overflow-hidden bg-white shadow-md hover:shadow-xl transition-all duration-200 group" onDoubleClick={handleDoubleClick}>
              {!imageLoaded && !imageError && (
                <div style={{ width: `${displayWidth}px` }} className="h-64 flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 animate-pulse">
                  <div className="flex flex-col items-center gap-2 text-gray-400">
                    <Upload className="w-6 h-6" />
                    <span className="text-sm">加载中...</span>
                  </div>
                </div>
              )}

              {imageError && (
                <div style={{ width: `${displayWidth}px` }} className="h-64 flex items-center justify-center bg-red-50 rounded-lg">
                  <div className="flex flex-col items-center gap-2 text-red-600">
                    <AlertCircle className="w-8 h-8" />
                    <span className="text-sm font-medium">图片加载失败</span>
                    <span className="text-xs text-red-500">请检查 URL 是否正确</span>
                  </div>
                </div>
              )}

              {/* 图片本体 */}
              <img
                ref={imgRef}
                src={url}
                alt={description || '预览'}
                onLoad={handleImageLoad}
                onError={handleImageError}
                className={`transition-transform duration-200 group-hover:scale-105 ${
                  imageError ? 'hidden' : ''
                }`}
                style={{ width: `${displayWidth}px`, height: 'auto' }}
              />

              {/* 加载完成标记 */}
              {imageLoaded && (
                <div className="absolute top-3 right-3 bg-green-500 text-white p-1.5 rounded-full shadow-lg animate-bounce">
                  <Check className="w-4 h-4" />
                </div>
              )}

              {/* Resize Handle - 右下角 */}
              {imageLoaded && !imageError && (
                <div
                  ref={resizeRef}
                  onMouseDown={handleMouseDown}
                  className="absolute bottom-0 right-0 w-4 h-4 bg-blue-500 hover:bg-blue-600 cursor-col-resize rounded-tl-md opacity-70 hover:opacity-100 transition-opacity"
                  title="拖拽调整图片大小，双击恢复默认"
                />
              )}
            </div>
          </div>

          {/* 右侧：描述文本框 */}
          <div className="flex-1 min-w-0 flex flex-col justify-between">
            {/* 描述输入框 - 填充整个高度 */}
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={handleSave}
              placeholder="输入图片的相关说明（可选）..."
              className="w-full p-3 border border-gray-300 rounded text-gray-900 text-sm resize-none flex-1 bg-white"
            />

            {/* 底部工具栏 */}
            <div className="flex items-center justify-between pt-3 border-t border-gray-200">
              {/* 左侧：尺寸显示 */}
              <div className="text-sm text-gray-600 font-medium">
                📏 {Math.round(displayWidth)} × {imageInfo.height ? Math.round((displayWidth / (imageInfo.width || 1)) * (imageInfo.height || 1)) : '?'}
              </div>

              {/* 右侧：操作按钮 */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleReplaceClick}
                  disabled={isReplacing}
                  className="px-3 py-1 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition disabled:opacity-50 flex items-center gap-1"
                  title="替换图片"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  替换
                </button>
                <button
                  onClick={handleSaveWidth}
                  className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition font-medium"
                  title="保存当前图片大小"
                >
                  ✓ 保存
                </button>
                {saveSuccess && (
                  <div className="text-xs text-green-600 font-medium animate-pulse">
                    ✓ 已保存
                  </div>
                )}
              </div>
            </div>

            {/* 隐藏的文件输入 */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
              disabled={isReplacing}
            />
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 p-4 bg-blue-50 border-2 border-dashed border-blue-300 rounded-lg">
          <Upload className="w-5 h-5 text-blue-500 flex-shrink-0" />
          <div className="text-sm text-blue-700">
            <p className="font-medium">还没有上传图片</p>
            <p className="text-blue-600 text-xs">点击编辑器工具栏的"插入图片"按钮上传</p>
          </div>
        </div>
      )}
    </div>
  );
}
