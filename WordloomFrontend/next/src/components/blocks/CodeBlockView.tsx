/**
 * CodeBlockView - 代码块视图（始终编辑状态）
 */
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Block, CodeBlock } from '@/modules/orbit/domain/blocks';
import { Copy, Check } from 'lucide-react';

interface CodeBlockViewProps {
  block: Block;
  onUpdate: (block: Block) => void;
}

export function CodeBlockView({
  block,
  onUpdate,
}: CodeBlockViewProps) {
  const code = block as CodeBlock;
  const [codeText, setCodeText] = useState(code.content.code || '');
  const [language, setLanguage] = useState(code.content.language || 'javascript');
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动调整高度
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    textarea.style.height = `${Math.max(textarea.scrollHeight, 100)}px`;
  }, [codeText]);

  const handleSave = () => {
    onUpdate({
      ...block,
      content: {
        ...code.content,
        code: codeText,
        language,
      },
      updatedAt: new Date().toISOString(),
    });
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(codeText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 justify-between">
        <select
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value);
            handleSave();
          }}
          className="px-2 py-1 border border-gray-300 rounded text-sm font-medium"
        >
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="python">Python</option>
          <option value="java">Java</option>
          <option value="cpp">C++</option>
          <option value="html">HTML</option>
          <option value="css">CSS</option>
          <option value="sql">SQL</option>
        </select>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 bg-gray-200 hover:bg-gray-300 rounded transition"
        >
          {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          {copied ? '已复制' : '复制'}
        </button>
      </div>
      <textarea
        ref={textareaRef}
        value={codeText}
        onChange={(e) => {
          setCodeText(e.target.value);
        }}
        onBlur={handleSave}
        placeholder="输入代码..."
        style={{
          minHeight: '100px',
          overflow: 'hidden',
          resize: 'none',
        }}
        className="w-full p-3 border border-blue-400 rounded font-mono text-sm text-gray-100 bg-gray-900 focus:ring-2 focus:ring-blue-500"
      />
      <div className="flex gap-2 text-xs text-gray-500">
        <span>自动保存（失焦时）</span>
      </div>
    </div>
  );
}
