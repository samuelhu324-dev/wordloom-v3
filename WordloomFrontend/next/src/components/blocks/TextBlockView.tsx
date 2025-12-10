'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Block } from '@/modules/orbit/domain/blocks';

interface TextBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
  noteId?: string;
}

/**
 * 文本块视图 - Inline 编辑，所见即所得
 */
export function TextBlockView({
  block,
  onUpdate,
  noteId,
}: TextBlockViewProps) {
  const initialText = (block.content?.text as string) || '';
  const [content, setContent] = useState(initialText);
  const [savedContent, setSavedContent] = useState(initialText);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const saveToastRef = useRef<NodeJS.Timeout | null>(null);

  // 当 block 改变时，更新初始值
  useEffect(() => {
    const newText = (block.content?.text as string) || '';
    setContent(newText);
    setSavedContent(newText);
  }, [block.id]);

  // 内容变化时更新状态（不立即保存）
  const handleChange = (newContent: string) => {
    setContent(newContent);
  };

  // 明确保存
  const handleSave = () => {
    console.log('[TextBlockView] 保存内容:', { content });
    onUpdate({
      ...block,
      content: {
        ...block.content,
        text: content,
      },
      updatedAt: new Date().toISOString(),
    });
    setSavedContent(content);
    setSaveSuccess(true);
    if (saveToastRef.current) clearTimeout(saveToastRef.current);
    saveToastRef.current = setTimeout(() => {
      setSaveSuccess(false);
    }, 2000);
  };

  // 恢复到上次保存的内容
  const handleReset = () => {
    setContent(savedContent);
  };

  const hasChanges = content !== savedContent;

  return (
    <div className="space-y-2">
      <textarea
        value={content}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="点击输入文本内容..."
        className="w-full p-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-300 resize-none bg-white hover:border-gray-400 transition"
        rows={Math.max(2, content.split('\n').length)}
        style={{ minHeight: '60px' }}
      />

      {/* 保存工具栏 */}
      <div className="flex items-center justify-end gap-2">
        <button
          onClick={handleReset}
          disabled={!hasChanges}
          className="px-2 py-1 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
          title="恢复到上次保存的内容"
        >
          ↻ 恢复
        </button>
        <button
          onClick={handleSave}
          className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition font-medium"
          title="保存内容"
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
  );
}
