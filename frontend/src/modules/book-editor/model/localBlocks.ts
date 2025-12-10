import type { BlockDto } from '@/entities/block';
import { parseFractionalIndex } from '@/features/block/lib/fractionalOrder';
import type { BlockEditorRenderable } from './BlockEditorContext';

const withClientId = (block: BlockDto | BlockEditorRenderable): BlockEditorRenderable => {
  const candidate = block as BlockEditorRenderable;
  return {
    ...block,
    __clientId: candidate.__clientId ?? block.id,
  };
};

const areContentsEqual = (
  a: BlockEditorRenderable['content'] | undefined,
  b: BlockDto['content'] | undefined,
) => {
  if (a === b) {
    return true;
  }
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    return false;
  }
};

const sortRenderables = (blocks: BlockEditorRenderable[]) => {
  return [...blocks].sort((a, b) => {
    const aVal = parseFractionalIndex(a.fractional_index) ?? Number.NEGATIVE_INFINITY;
    const bVal = parseFractionalIndex(b.fractional_index) ?? Number.NEGATIVE_INFINITY;
    if (aVal === bVal) {
      return a.__clientId.localeCompare(b.__clientId);
    }
    return aVal - bVal;
  });
};

export const upsertRenderableBlock = (
  blocks: BlockEditorRenderable[],
  block: BlockDto | BlockEditorRenderable,
) => {
  const next = withClientId(block);
  const existingIndex = blocks.findIndex((item) => item.id === next.id);
  if (existingIndex >= 0) {
    const updated = [...blocks];
    updated[existingIndex] = next;
    return sortRenderables(updated);
  }
  return sortRenderables([...blocks, next]);
};

export const removeRenderableBlock = (blocks: BlockEditorRenderable[], blockId: string) => {
  return blocks.filter((block) => block.id !== blockId);
};

export const attachRenderableMeta = (block: BlockDto | BlockEditorRenderable) => {
  return withClientId(block);
};

export const reconcileRenderableBlocks = (
  current: BlockEditorRenderable[],
  incoming: BlockDto[],
) => {
  if (!incoming.length) {
    return [];
  }
  if (!current.length) {
    return incoming.map((block) => attachRenderableMeta(block));
  }
  const currentMap = new Map(current.map((block) => [block.id, block]));
  const merged = incoming.map((block) => {
    const existing = currentMap.get(block.id);
    if (!existing) {
      return attachRenderableMeta(block);
    }
    const contentMatches = areContentsEqual(existing.content, block.content);
    const fractionalMatches = existing.fractional_index === block.fractional_index;
    const kindMatches = existing.kind === block.kind;
    const headingMatches = existing.heading_level === block.heading_level;

    if (contentMatches && fractionalMatches && kindMatches && headingMatches) {
      return existing;
    }

    return withClientId({
      ...block,
      __clientId: existing.__clientId,
      content: contentMatches ? existing.content : block.content,
    });
  });
  return sortRenderables(merged);
};
