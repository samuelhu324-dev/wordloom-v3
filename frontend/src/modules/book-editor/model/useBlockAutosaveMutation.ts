'use client';

import React from 'react';
import { useMutation } from '@tanstack/react-query';
import type { UpdateBlockRequest } from '@/entities/block';
import { updateBlock } from '@/features/block/model/api';
import { useBlockEditorContext, type BlockEditorRenderable } from './BlockEditorContext';
import { upsertRenderableBlock } from './localBlocks';

export const useBlockAutosaveMutation = (blockId: string) => {
  const { blocks, setBlocks } = useBlockEditorContext();
  const latestBlockRef = React.useRef<BlockEditorRenderable | null>(null);

  React.useEffect(() => {
    latestBlockRef.current = blocks.find((block) => block.id === blockId) ?? null;
  }, [blocks, blockId]);

  return useMutation({
    mutationFn: (request: UpdateBlockRequest) => updateBlock(blockId, request),
    onSuccess: (updated) => {
      const latest = latestBlockRef.current;
      if (latest && latest.kind !== updated.kind) {
        if (process.env.NODE_ENV !== 'production') {
          console.warn('[autosave] stale response ignored', {
            blockId,
            latestKind: latest.kind,
            responseKind: updated.kind,
          });
        }
        return;
      }
      const merged = latest ? { ...updated, kind: latest.kind } : updated;
      setBlocks((prev) => upsertRenderableBlock(prev, merged));
    },
  });
};
