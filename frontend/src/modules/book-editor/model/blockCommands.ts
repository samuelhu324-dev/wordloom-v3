"use client";

import React from 'react';
import type { BlockContent, BlockKind } from '@/entities/block';
import { serializeBlockContent } from '@/entities/block';
import { useDeleteBlock } from '@/features/block/model/hooks';
import { updateBlock as updateBlockApi } from '@/features/block/model/api';
import type { InsertPosition, InsertBlockOptions } from './insertController';
import { useBlockInsertController } from './insertController';
import { useBlockEditorContext, type BlockEditorRenderable } from './BlockEditorContext';
import { attachRenderableMeta, removeRenderableBlock, upsertRenderableBlock } from './localBlocks';
import { announceFocusIntent, type SelectionEdge } from './selectionStore';
import { isRenderableBlockEmpty } from './isRenderableBlockEmpty';
import {
  BASE_BLOCK_KIND,
  createDefaultContentForKind,
  deriveParagraphContentFromRenderable,
  isBaseBlockKind,
  isSpecialBlockKind,
} from './blockKindRules';

interface CreateBlockCommandOptions {
  kind?: BlockKind;
  contentOverride?: BlockContent;
  headingLevel?: 1 | 2 | 3;
  position?: InsertPosition;
  selectionEdge?: SelectionEdge;
  onCreated?: (blockId: string) => void;
}

interface DeleteBlockCommandOptions {
  blockId: string;
  selectionFallback?: { blockId: string; edge: SelectionEdge };
  silent?: boolean;
}

interface BlockCommands {
  createBlock: (options?: CreateBlockCommandOptions) => Promise<BlockEditorRenderable>;
  deleteBlock: (options: DeleteBlockCommandOptions) => Promise<void>;
  transformBlock: (options: TransformBlockCommandOptions) => Promise<BlockEditorRenderable | null>;
}

type DeleteIntent = 'keyboard' | 'menu' | 'toolbar' | 'system';

interface DeleteBlockWithGuardOptions {
  blockId: string;
  intent?: DeleteIntent;
  allowDowngrade?: boolean;
}

interface TransformBlockCommandOptions {
  blockId: string;
  targetKind: BlockKind;
  contentOverride?: BlockContent;
  selectionEdge?: SelectionEdge;
  source?: string;
}

type DeleteBlockWithGuardResult =
  | { status: 'deleted'; blockId: string }
  | { status: 'downgraded'; blockId: string; replacementBlockId?: string }
  | { status: 'cleared'; blockId: string }
  | { status: 'noop'; blockId?: string };

export const useBlockCommands = (): BlockCommands => {
  const { bookId, blocks, setBlocks } = useBlockEditorContext();
  const { insertBlock } = useBlockInsertController();
  const deleteMutation = useDeleteBlock();

  const createBlock = React.useCallback(async (options?: CreateBlockCommandOptions) => {
    if (!bookId) {
      throw new Error('Missing bookId for createBlock command');
    }

    const payload: InsertBlockOptions = {
      bookId,
      kind: options?.kind,
      contentOverride: options?.contentOverride,
      headingLevel: options?.headingLevel,
      position: options?.position,
    };

    const created = attachRenderableMeta(await insertBlock(payload));
    setBlocks((prev) => upsertRenderableBlock(prev, created));
    if (options?.selectionEdge) {
      announceFocusIntent('keyboard', created.id, {
        payload: { edge: options.selectionEdge },
        source: 'block-commands.create-block',
      });
    }
    options?.onCreated?.(created.id);
    return created;
  }, [bookId, insertBlock, setBlocks]);

  const deleteBlock = React.useCallback(async (options: DeleteBlockCommandOptions) => {
    let removed: BlockEditorRenderable | null = null;
    let needsReplacement = false;

    setBlocks((prev) => {
      const target = prev.find((item) => item.id === options.blockId) ?? null;
      removed = target;
      if (!target) {
        return prev;
      }
      if (prev.length === 1) {
        needsReplacement = true;
        return prev;
      }
      return removeRenderableBlock(prev, options.blockId);
    });

    if (!removed) {
      return;
    }
    const removedBlock: BlockEditorRenderable = removed;

    if (needsReplacement) {
      let replacement: BlockEditorRenderable | null = null;
      try {
        replacement = await createBlock({
          kind: 'paragraph',
          position: {
            rank: Number.parseFloat(removedBlock.fractional_index) || 1,
          },
          selectionEdge: 'start',
        });
      } catch (error) {
        console.error('创建兜底段落失败', error);
        throw error;
      }

      setBlocks((prev) => removeRenderableBlock(prev, removedBlock.id));

      try {
        await deleteMutation.mutateAsync(options.blockId);
      } catch (error) {
        console.error('删除块失败', error);
        setBlocks((prev) => upsertRenderableBlock(prev, removedBlock));
        if (replacement) {
          setBlocks((prev) => removeRenderableBlock(prev, replacement!.id));
          try {
            await deleteMutation.mutateAsync(replacement.id);
          } catch (cleanupError) {
            console.error('回滚兜底段落失败', cleanupError);
          }
        }
        throw error;
      }

      return;
    }

    if (options.selectionFallback) {
      announceFocusIntent('keyboard', options.selectionFallback.blockId, {
        payload: { edge: options.selectionFallback.edge },
        source: 'block-commands.delete-fallback',
      });
    }

    try {
      await deleteMutation.mutateAsync(options.blockId);
    } catch (error) {
      console.error('删除块失败', error);
      setBlocks((prev) => upsertRenderableBlock(prev, removedBlock));
      throw error;
    }
  }, [createBlock, deleteMutation, setBlocks]);

  const transformBlock = React.useCallback(async (options: TransformBlockCommandOptions) => {
    const targetIndex = blocks.findIndex((candidate) => candidate.id === options.blockId);
    if (targetIndex === -1) {
      return null;
    }
    const current = blocks[targetIndex];
    const nextContent = options.contentOverride ?? createDefaultContentForKind(options.targetKind);
    const serialized = serializeBlockContent(options.targetKind, nextContent);
    const updated: BlockEditorRenderable = { ...current, kind: options.targetKind, content: nextContent };
    setBlocks((prev) => upsertRenderableBlock(prev, updated));
    try {
      await updateBlockApi(current.id, { kind: options.targetKind, content: serialized });
    } catch (error) {
      console.error('变更块类型失败', error);
      setBlocks((prev) => upsertRenderableBlock(prev, current));
      throw error;
    }
    if (options.selectionEdge) {
      announceFocusIntent('keyboard', current.id, {
        payload: { edge: options.selectionEdge },
        source: options.source ?? 'block-commands.transform',
      });
    }
    return updated;
  }, [blocks, setBlocks]);

  return { createBlock, deleteBlock, transformBlock };
};

/**
 * Provides the guarded delete command that enforces single-block safeguards, downgrade rules,
 * and focus fallbacks. Only block-shell components (e.g. BlockItem) should call this hook.
 */
export const useBlockDeleteGuard = (): ( (
  options: DeleteBlockWithGuardOptions,
) => Promise<DeleteBlockWithGuardResult> ) => {
  const { blocks, setBlocks } = useBlockEditorContext();
  const { deleteBlock } = useBlockCommands();

  const computeFallback = React.useCallback((targetIndex: number) => {
    if (blocks.length <= 1) {
      return undefined;
    }
    const previous = blocks[targetIndex - 1];
    if (previous) {
      return { blockId: previous.id, edge: 'end' as SelectionEdge };
    }
    const next = blocks[targetIndex + 1];
    if (next) {
      return { blockId: next.id, edge: 'start' as SelectionEdge };
    }
    return undefined;
  }, [blocks]);

  const downgradeBlockToParagraph = React.useCallback(async (
    block: BlockEditorRenderable,
    source: string,
  ) => {
    const nextContent = deriveParagraphContentFromRenderable(block);
    const serialized = serializeBlockContent(BASE_BLOCK_KIND, nextContent);
    const downgraded: BlockEditorRenderable = { ...block, kind: BASE_BLOCK_KIND, content: nextContent };
    setBlocks((prev) => upsertRenderableBlock(prev, downgraded));
    try {
      await updateBlockApi(block.id, { kind: BASE_BLOCK_KIND, content: serialized });
    } catch (error) {
      console.error('降级特殊块失败', error);
      setBlocks((prev) => upsertRenderableBlock(prev, block));
      throw error;
    }
    announceFocusIntent('keyboard', block.id, {
      payload: { edge: 'end' },
      source,
    });
    return downgraded;
  }, [setBlocks]);

  const clearSingleBaseBlock = React.useCallback(async (block: BlockEditorRenderable) => {
    if (!isBaseBlockKind(block.kind)) {
      return;
    }
    const emptyContent = { text: '' } satisfies BlockContent;
    const serialized = serializeBlockContent(BASE_BLOCK_KIND, emptyContent);
    setBlocks((prev) => upsertRenderableBlock(prev, { ...block, content: emptyContent }));
    try {
      await updateBlockApi(block.id, { content: serialized });
    } catch (error) {
      console.error('清空基础块失败', error);
      setBlocks((prev) => upsertRenderableBlock(prev, block));
      throw error;
    }
  }, [setBlocks]);

  const deleteBlockWithGuard = React.useCallback(async (
    options: DeleteBlockWithGuardOptions,
  ): Promise<DeleteBlockWithGuardResult> => {
    const targetIndex = blocks.findIndex((candidate) => candidate.id === options.blockId);
    if (targetIndex === -1) {
      return { status: 'noop' };
    }
    const target = blocks[targetIndex];
    const fallback = computeFallback(targetIndex);
    const isOnlyBlock = blocks.length === 1;
    const allowDowngrade = options.allowDowngrade !== false;
    const empty = isRenderableBlockEmpty(target);

    if (isOnlyBlock) {
      if (isBaseBlockKind(target.kind)) {
        if (empty) {
          return { status: 'noop', blockId: target.id };
        }
        await clearSingleBaseBlock(target);
        announceFocusIntent('keyboard', target.id, {
          payload: { edge: 'start' },
          source: 'block-commands.guard.base-single',
        });
        return { status: 'cleared', blockId: target.id };
      }
      if (allowDowngrade) {
        await downgradeBlockToParagraph(target, 'block-commands.guard.single-special');
        return { status: 'downgraded', blockId: target.id };
      }
      return { status: 'noop', blockId: target.id };
    }

    if (isSpecialBlockKind(target.kind)) {
      if (allowDowngrade) {
        await downgradeBlockToParagraph(target, 'block-commands.guard.multi-special');
        return { status: 'downgraded', blockId: target.id };
      }
      await deleteBlock({ blockId: target.id, selectionFallback: fallback });
      return { status: 'deleted', blockId: target.id };
    }

    await deleteBlock({ blockId: target.id, selectionFallback: fallback });
    return { status: 'deleted', blockId: target.id };
  }, [blocks, clearSingleBaseBlock, computeFallback, deleteBlock, downgradeBlockToParagraph]);

  return deleteBlockWithGuard;
};
