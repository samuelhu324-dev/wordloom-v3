import type { BlockEditorCoreHandle } from '../ui/BlockEditorCore';

type HandleProvider = () => BlockEditorCoreHandle | null;

const registry = new Map<string, HandleProvider>();

export const registerBlockEditorHandle = (blockId: string, provider: HandleProvider) => {
  registry.set(blockId, provider);
};

export const unregisterBlockEditorHandle = (blockId: string) => {
  registry.delete(blockId);
};

export const getBlockEditorHandle = (blockId: string): BlockEditorCoreHandle | null => {
  const provider = registry.get(blockId);
  return provider ? provider() : null;
};
