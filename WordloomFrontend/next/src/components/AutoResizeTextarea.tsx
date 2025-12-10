/**
 * AutoResizeTextarea - 根据内容自动调整高度的 textarea 组件
 * 使用 CSS Grid 技巧实现无缝的高度自适应
 */
'use client';

import React, { useEffect, useRef } from 'react';

interface AutoResizeTextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  value: string;
  minHeight?: string; // 最小高度，默认 "60px"
}

export function AutoResizeTextarea({
  value,
  minHeight = '60px',
  className = '',
  ...props
}: AutoResizeTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 自动调整高度的效果
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // 重置高度以获取实际的 scrollHeight
    textarea.style.height = 'auto';
    // 设置为 scrollHeight，即内容实际需要的高度
    textarea.style.height = `${Math.max(textarea.scrollHeight, parseInt(minHeight))}px`;
  }, [value, minHeight]);

  return (
    <textarea
      ref={textareaRef}
      value={value}
      style={{
        minHeight,
        overflow: 'hidden', // 隐藏滚动条，因为高度会自动调整
        resize: 'none', // 禁用手动调整大小
      }}
      className={`w-full p-3 border border-blue-400 rounded focus:ring-2 focus:ring-blue-500 text-gray-900 leading-relaxed font-medium transition-all ${className}`}
      {...props}
    />
  );
}
