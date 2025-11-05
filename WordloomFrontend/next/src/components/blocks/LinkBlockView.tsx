/**
 * LinkBlockView - 链接块视图（始终编辑状态）
 */
'use client';

import React, { useState } from 'react';
import { Block, LinkBlock } from '@/modules/orbit/domain/blocks';
import { ExternalLink } from 'lucide-react';

interface LinkBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
}

export function LinkBlockView({
  block,
  onUpdate,
}: LinkBlockViewProps) {
  const link = block as LinkBlock;
  const [url, setUrl] = useState(link.content.url || '');
  const [title, setTitle] = useState(link.content.title || '');

  const handleSave = () => {
    onUpdate({
      ...block,
      content: {
        ...link.content,
        url,
        title,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  return (
    <div className="space-y-2">
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        onBlur={handleSave}
        placeholder="输入链接 URL..."
        className="w-full p-2 border border-blue-400 rounded focus:ring-2 focus:ring-blue-500 text-gray-900 text-sm"
      />
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onBlur={handleSave}
        placeholder="输入链接标题（可选）..."
        className="w-full p-2 border border-gray-300 rounded text-gray-900 text-sm"
      />
      {url && (
        <div className="flex items-center gap-2 p-2 bg-blue-50 border border-blue-200 rounded">
          <ExternalLink className="w-4 h-4 text-blue-600" />
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 hover:underline text-sm truncate"
          >
            {title || url}
          </a>
        </div>
      )}
      <div className="flex gap-2 text-xs text-gray-500">
        <span>自动保存（失焦时）</span>
      </div>
    </div>
  );
}
