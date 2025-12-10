import React, { useState, useRef } from 'react';
import { Upload, X } from 'lucide-react';

interface NotePreviewPickerProps {
  note: any;  // Note 对象
  isOpen: boolean;
  onClose: () => void;
  onPreviewUploaded: (imageUrl: string) => void;
}

/**
 * 笔记预览图上传器
 * 用户可以上传一张新图片作为笔记的预览/封面图
 * 图片保存在 storage/orbit_uploads/notes/{note_id}/cover/cover.png
 */
export const NotePreviewPicker: React.FC<NotePreviewPickerProps> = ({
  note,
  isOpen,
  onClose,
  onPreviewUploaded,
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen || !note?.id) {
    return null;
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }

    setIsUploading(true);
    try {
      console.log('[NotePreviewPicker] 开始上传封面图:', {
        noteId: note.id,
        filename: file.name,
        size: file.size,
        type: file.type,
      });

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`/api/orbit/uploads/note/${note.id}/cover`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`上传失败: ${error}`);
      }

      const data = await response.json();
      console.log('[NotePreviewPicker] ✓ 封面图上传成功:', data);
      console.log('[NotePreviewPicker] 返回的 URL:', data.url);
      console.log('[NotePreviewPicker] 调用 onPreviewUploaded 回调');

      onPreviewUploaded(data.url);
      onClose();
    } catch (err) {
      console.error('[NotePreviewPicker] ✗ 上传失败:', err);
      alert(`上传失败: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
      // 重置文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <>
      {/* 背景遮罩 */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        onClick={onClose}
      >
        {/* 对话框 */}
        <div
          className="bg-white rounded-lg max-w-sm w-full shadow-xl mx-4"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 标题栏 */}
          <div className="border-b p-4 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-800">上传封面图</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            >
              ✕
            </button>
          </div>

          {/* 内容 */}
          <div className="p-6">
            {/* 上传区域 */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="w-full border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Upload size={40} className="mx-auto text-gray-400 mb-3" />
              <p className="text-gray-700 font-medium mb-1">点击上传图片</p>
              <p className="text-sm text-gray-500">支持 PNG, JPG, GIF 等格式</p>
            </button>

            {/* 隐藏的文件输入 */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="hidden"
              disabled={isUploading}
            />
          </div>

          {/* 底部按钮 */}
          <div className="border-t p-4 flex justify-end gap-2">
            <button
              onClick={onClose}
              disabled={isUploading}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition disabled:opacity-50"
            >
              {isUploading ? '上传中...' : '关闭'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
