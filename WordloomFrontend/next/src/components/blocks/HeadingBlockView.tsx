/**
 * HeadingBlockView - 标题块视图（始终编辑状态）
 */
'use client';

import React, { useState } from 'react';
import { Block, HeadingBlock } from '@/modules/orbit/domain/blocks';

interface HeadingBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
}

export function HeadingBlockView({
  block,
  onUpdate,
}: HeadingBlockViewProps) {
  const heading = block as HeadingBlock;
  const [text, setText] = useState(heading.content.text || '');
  const [level, setLevel] = useState<1 | 2 | 3 | 4 | 5 | 6>(heading.content.level || 2);

  const handleSave = () => {
    onUpdate({
      ...block,
      content: {
        ...block.content,
        text,
        level,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  const sizeClasses: Record<number, string> = {
    1: 'text-3xl font-bold',
    2: 'text-2xl font-bold',
    3: 'text-xl font-bold',
    4: 'text-lg font-semibold',
    5: 'text-base font-semibold',
    6: 'text-sm font-semibold',
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSave();
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2 items-center">
        <label className="text-xs text-gray-600 font-medium">标题级别：</label>
        <select
          value={level}
          onChange={(e) => {
            const newLevel = parseInt(e.target.value) as 1 | 2 | 3 | 4 | 5 | 6;
            setLevel(newLevel);
            onUpdate({
              ...block,
              content: {
                ...heading.content,
                text,
                level: newLevel,
              },
              updatedAt: new Date().toISOString(),
            });
          }}
          className="px-2 py-1 border border-gray-300 rounded text-sm font-medium"
        >
          {[1, 2, 3, 4, 5, 6].map((l) => (
            <option key={l} value={l}>
              H{l}
            </option>
          ))}
        </select>
      </div>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleSave}
        placeholder="输入标题..."
        className={`w-full p-2 border border-blue-400 rounded focus:ring-2 focus:ring-blue-500 text-gray-900 font-medium ${sizeClasses[level]}`}
      />
      <div className="flex gap-2 text-xs text-gray-500">
        <span>Ctrl+Enter 保存</span>
        <span>自动保存（失焦时）</span>
      </div>
    </div>
  );
}
