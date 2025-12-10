// LEGACY: Support helpers for the deprecated block editor stack.
import React from 'react';
import type { BlockContent, BlockDto, BlockKind } from '@/entities/block';
import type { InsertBlockHandler } from './insertTypes';

export interface BlockDisplayProps {
  block: BlockDto;
  content: BlockContent;
  onStartEdit: () => void;
  onChange: (nextContent: BlockContent) => void;
  onQuickSave?: () => Promise<void> | void;
}

export interface BlockEditorProps {
  block: BlockDto;
  content: BlockContent;
  editorRef?: React.RefObject<HTMLElement | null>;
  onChange: (nextContent: BlockContent) => void;
  onSave: () => Promise<void> | void;
  onExitEdit: () => void;
  onCancelEdit: () => void;
  onInsertBlock?: InsertBlockHandler;
  onTransformBlock?: (kind: BlockKind, content: BlockContent) => void;
  onDeleteBlock?: () => void;
}

export interface BlockPlugin {
  kind: BlockKind;
  Display: React.FC<BlockDisplayProps>;
  Editor: React.FC<BlockEditorProps>;
  createDefaultContent: () => BlockContent;
}

const registry: Partial<Record<BlockKind, BlockPlugin>> = {};

export const registerBlockPlugin = (plugin: BlockPlugin) => {
  registry[plugin.kind] = plugin;
};

export const getBlockPlugin = (kind: BlockKind): BlockPlugin | null => {
  return registry[kind] ?? null;
};

export const getDefaultContentForKind = (kind: BlockKind): BlockContent | null => {
  const plugin = registry[kind];
  return plugin?.createDefaultContent() ?? null;
};
