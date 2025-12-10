/**
 * ParagraphBlockView - 段落块视图（始终编辑状态）
 * 仅用于编辑文本内容，图片由 ImageBlock 负责
 */
'use client';

import React, { useState } from 'react';
import { Block } from '@/modules/orbit/domain/blocks';
import { AutoResizeTextarea } from '@/components/AutoResizeTextarea';

interface ParagraphBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
}

export function ParagraphBlockView({
  block,
  onUpdate,
}: ParagraphBlockViewProps) {
  const [text, setText] = useState(block.content.text || '');

  const handleSave = () => {
    onUpdate({
      ...block,
      content: {
        ...block.content,
        text,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSave();
    }
  };

  return (
    <div className="space-y-2">
      <AutoResizeTextarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleSave}
        placeholder="输入段落内容..."
        minHeight="80px"
      />
      <div className="flex gap-2 text-xs text-gray-500">
        <span>Ctrl+Enter 保存</span>
        <span>自动保存（失焦时）</span>
      </div>
    </div>
  );
}