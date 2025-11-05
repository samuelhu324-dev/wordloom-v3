'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Save } from 'lucide-react';

interface FloatingSaveBarProps {
  onSave: () => Promise<void>;
}

export function FloatingSaveBar({ onSave }: FloatingSaveBarProps) {
  const [isSaving, setIsSaving] = useState(false);

  // 处理保存逻辑（按钮和快捷键都用这个）
  const handleSave = useCallback(async () => {
    if (isSaving) return;

    try {
      setIsSaving(true);
      await onSave();
      console.log('[FloatingSaveBar] 保存成功');
    } catch (error) {
      console.error('[FloatingSaveBar] 保存失败:', error);
      alert(`保存失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setIsSaving(false);
    }
  }, [onSave, isSaving]);

  // 监听 Ctrl+S 快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSave]);

  return (
    <button
      onClick={handleSave}
      disabled={isSaving}
      className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200"
      title="保存 (Ctrl+S)"
    >
      <Save className="w-4 h-4" />
      {isSaving ? '保存中...' : '保存'}
    </button>
  );
}
