/**
 * BlockRenderer - 根据 block 类型动态渲染对应的组件
 */
'use client';

import React from 'react';
import { Block, getBlockPreview } from '@/modules/orbit/domain/blocks';
import { ParagraphBlockView } from './blocks/ParagraphBlockView';
import { HeadingBlockView } from './blocks/HeadingBlockView';
import { CheckpointBlockView } from './blocks/CheckpointBlockView';
import { ImageBlockView } from './blocks/ImageBlockView';
import { LinkBlockView } from './blocks/LinkBlockView';
import { QuoteBlockView } from './blocks/QuoteBlockView';
import { CodeBlockView } from './blocks/CodeBlockView';
import { TableBlockView } from './blocks/TableBlockView';
import { TextBlockView } from './blocks/TextBlockView';
import { Trash2, GripVertical, ChevronUp, ChevronDown } from 'lucide-react';

interface BlockRendererProps {
  block: Block;
  onUpdate: (block: Block) => void;
  onDelete: () => void;
  isDragging?: boolean;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: () => void;
  isFirst?: boolean;
  isLast?: boolean;
  onMoveUp?: () => void;
  onMoveDown?: () => void;
  noteId?: string; // 笔记 ID，用于 CheckpointBlockView
  onSave?: () => Promise<void>; // 保存回调
}

/**
 * 主 Block 渲染器
 * 根据 block 类型选择对应的视图组件
 */
export function BlockRenderer({
  block,
  onUpdate,
  onDelete,
  isDragging = false,
  onDragStart,
  onDragEnd,
  isFirst = false,
  isLast = false,
  onMoveUp,
  onMoveDown,
  noteId,
  onSave,
}: BlockRendererProps) {
  const renderBlockContent = () => {
    switch (block.type) {
      case 'paragraph':
        return (
          <ParagraphBlockView
            block={block}
            onUpdate={onUpdate}
          />
        );
      case 'heading':
        return (
          <HeadingBlockView
            block={block}
            onUpdate={onUpdate}
          />
        );
      case 'checkpoint':
        return (
          <CheckpointBlockView
            block={block}
            onUpdate={onUpdate}
            noteId={noteId}
            onSave={onSave}
          />
        );
      case 'image':
        return (
          <ImageBlockView
            block={block}
            onUpdate={onUpdate}
            noteId={noteId}
          />
        );
      case 'link':
        return (
          <LinkBlockView
            block={block}
            onUpdate={onUpdate}
          />
        );
      case 'quote':
        return (
          <QuoteBlockView
            block={block}
            onUpdate={onUpdate}
          />
        );
      case 'code':
        return (
          <CodeBlockView
            block={block}
            onUpdate={onUpdate}
          />
        );
      case 'table':
        return (
          <TableBlockView
            block={block}
            onUpdate={onUpdate}
          />
        );
      case 'text':
        return (
          <TextBlockView
            block={block}
            onUpdate={onUpdate}
          />
        );
      default:
        return <div className="text-red-500">未支持的 block 类型: {block.type}</div>;
    }
  };

  return (
    <div
      className={`group relative border rounded-lg transition flex ${
        isDragging
          ? 'bg-blue-50 border-blue-300 opacity-50'
          : 'bg-white border-gray-300 hover:border-blue-400 hover:shadow-md'
      }`}
      data-block-id={block.id}
      data-block-type={block.type}
    >
      {/* 左侧拖拽把手 - 竖条式 */}
      <div
        draggable
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
        className="w-6 flex-shrink-0 flex items-center justify-center cursor-grab active:cursor-grabbing
                   hover:bg-gray-200 text-gray-400 hover:text-gray-600 transition-colors"
        title="拖拽移动"
      >
        <span className="text-sm font-bold">≡≡</span>
      </div>

      {/* 内容区 */}
      <div className="flex-1 p-4">
        {renderBlockContent()}
      </div>

      {/* 右侧操作按钮 */}
      <div className="absolute -right-16 top-3 flex flex-col items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {!isFirst && (
          <button
            onClick={onMoveUp}
            className="px-2 py-1 text-xs text-gray-500 hover:bg-blue-50 hover:text-blue-600 rounded transition"
            title="向上移动"
          >
            <ChevronUp className="w-4 h-4" />
          </button>
        )}
        {!isLast && (
          <button
            onClick={onMoveDown}
            className="px-2 py-1 text-xs text-gray-500 hover:bg-blue-50 hover:text-blue-600 rounded transition"
            title="向下移动"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        )}
        <button
          onClick={onDelete}
          className="px-2 py-1 text-xs text-red-500 hover:bg-red-50 rounded transition"
          title="删除 block"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

/**
 * BlockContainer - Block 列表容器，支持拖拽排序
 */
interface BlockContainerProps {
  blocks: Block[];
  onUpdateBlock: (blockId: string, block: Block) => void;
  onDeleteBlock: (blockId: string) => void;
  onReorderBlocks?: (fromIndex: number, toIndex: number) => void;
  noteId?: string; // 笔记 ID，传给子组件
  fallbackText?: string; // 当 blocks 为空时显示的 fallback 文本内容
  onSave?: () => Promise<void>; // 保存回调，用于 Ctrl+S 和浮动保存栏
}

export function BlockContainer({
  blocks,
  onUpdateBlock,
  onDeleteBlock,
  onReorderBlocks,
  noteId,
  fallbackText,
  onSave,
}: BlockContainerProps) {
  const [draggedBlockId, setDraggedBlockId] = React.useState<string | null>(null);
  const [dragOverIndex, setDragOverIndex] = React.useState<number | null>(null);

  const handleDragStart = (e: React.DragEvent, blockId: string) => {
    setDraggedBlockId(blockId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    setDragOverIndex(index);
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (!draggedBlockId || !onReorderBlocks) return;

    const fromIndex = blocks.findIndex((b) => b.id === draggedBlockId);
    if (fromIndex !== -1 && fromIndex !== index) {
      onReorderBlocks(fromIndex, index);
    }

    setDraggedBlockId(null);
    setDragOverIndex(null);
  };

  const handleDragLeave = () => {
    setDragOverIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedBlockId(null);
    setDragOverIndex(null);
  };

  // 如果 blocks 为空，显示 fallback text 或提示信息
  if (blocks.length === 0) {
    if (fallbackText) {
      // 有 fallback text 时，显示为可编辑的文本区域
      return (
        <div className="space-y-3">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-sm font-semibold text-yellow-900 mb-2">
              ℹ️ 内容检测到但尚未转换为块格式
            </div>
            <div className="bg-white rounded p-3 border border-yellow-100 text-sm text-gray-700 whitespace-pre-wrap font-mono overflow-auto max-h-64">
              {fallbackText}
            </div>
            <div className="mt-3 text-xs text-yellow-700">
              💡 这是原始内容的预览。点击下方"添加块"按钮开始以块的形式编辑内容。
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="p-8 text-center text-gray-400 border-2 border-dashed border-gray-200 rounded-lg">
        <p>没有内容块。点击下方工具栏添加第一个块。</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {blocks.map((block, index) => (
        <div
          key={block.id}
          onDragOver={(e) => handleDragOver(e, index)}
          onDrop={(e) => handleDrop(e, index)}
          onDragLeave={handleDragLeave}
          className={`transition ${
            dragOverIndex === index ? 'py-4 border-t-2 border-blue-400' : ''
          }`}
        >
          <BlockRenderer
            block={block}
            onUpdate={(updated) => onUpdateBlock(block.id, updated)}
            onDelete={() => onDeleteBlock(block.id)}
            isDragging={draggedBlockId === block.id}
            onDragStart={(e) => handleDragStart(e, block.id)}
            onDragEnd={handleDragEnd}
            isFirst={index === 0}
            isLast={index === blocks.length - 1}
            noteId={noteId}
            onSave={onSave}
            onMoveUp={() => {
              if (index > 0 && onReorderBlocks) {
                onReorderBlocks(index, index - 1);
              }
            }}
            onMoveDown={() => {
              if (index < blocks.length - 1 && onReorderBlocks) {
                onReorderBlocks(index, index + 1);
              }
            }}
          />
        </div>
      ))}
    </div>
  );
}
