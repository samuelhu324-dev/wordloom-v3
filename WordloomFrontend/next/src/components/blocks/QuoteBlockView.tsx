/**
 * QuoteBlockView - 引用块视图（始终编辑状态）
 */
'use client';

import React, { useState } from 'react';
import { Block, QuoteBlock } from '@/modules/orbit/domain/blocks';
import { AutoResizeTextarea } from '@/components/AutoResizeTextarea';

interface QuoteBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
}

export function QuoteBlockView({
  block,
  onUpdate,
}: QuoteBlockViewProps) {
  const quote = block as QuoteBlock;
  const [text, setText] = useState(quote.content.text || '');
  const [author, setAuthor] = useState(quote.content.author || '');

  const handleSave = () => {
    onUpdate({
      ...block,
      content: {
        ...quote.content,
        text,
        author,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  return (
    <div className="space-y-2">
      <AutoResizeTextarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={handleSave}
        placeholder="输入引用内容..."
        minHeight="60px"
      />
      <input
        type="text"
        value={author}
        onChange={(e) => setAuthor(e.target.value)}
        onBlur={handleSave}
        placeholder="作者（可选）..."
        className="w-full p-2 border border-gray-300 rounded text-sm text-gray-700"
      />
      <div className="flex gap-2 text-xs text-gray-500">
        <span>自动保存（失焦时）</span>
      </div>
    </div>
  );
}
