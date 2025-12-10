import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { BlockContent, BlockKind } from '@/entities/block';
import { createDefaultBlockContent, serializeBlockContent } from '@/entities/block';
import { useCreateBlock, useReorderBlock } from '@/features/block/model/hooks';
import { computeFractionalIndex } from '@/features/block/lib/fractionalOrder';

export interface InsertPosition {
  before?: string;
  after?: string;
  rank?: number;
}

export interface InsertBlockOptions {
  bookId: string;
  kind?: BlockKind;
  contentOverride?: BlockContent;
  headingLevel?: 1 | 2 | 3;
  position?: InsertPosition;
}

export const useBlockInsertController = () => {
  const queryClient = useQueryClient();
  const createBlock = useCreateBlock();
  const reorderBlock = useReorderBlock();

  const insertBlock = React.useCallback(async (options: InsertBlockOptions) => {
    const {
      bookId,
      kind = 'paragraph',
      contentOverride,
      headingLevel,
      position,
    } = options;

    if (!bookId) {
      throw new Error('missing bookId when inserting block');
    }

    const baseContent = contentOverride ?? createDefaultBlockContent(kind);
    const serialized = serializeBlockContent(kind, baseContent);
    const created = await createBlock.mutateAsync({
      book_id: bookId,
      kind,
      content: serialized,
      ...(headingLevel ? { heading_level: headingLevel } : {}),
    });

    const newOrder = computeFractionalIndex(
      position?.before,
      position?.after,
      position?.rank ?? 1,
    );

    if (newOrder) {
      try {
        await reorderBlock.mutateAsync({ blockId: created.id, newOrder });
      } catch (error) {
        console.warn('插入块时重新排序失败', error);
      }
    }

    void queryClient.invalidateQueries({ queryKey: ['blocks'] });

    return {
      ...created,
      fractional_index: newOrder ?? created.fractional_index,
    };
  }, [createBlock, reorderBlock, queryClient]);

  return {
    insertBlock,
    isInserting: createBlock.isPending,
  };
};
