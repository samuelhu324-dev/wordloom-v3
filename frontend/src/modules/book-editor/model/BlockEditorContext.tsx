"use client";

import React from 'react';
import type { BlockDto } from '@/entities/block';

export type BlockEditorRenderable = BlockDto & { __clientId: string };

export interface BlockEditorContextValue {
  bookId: string;
  blocks: BlockEditorRenderable[];
  setBlocks: React.Dispatch<React.SetStateAction<BlockEditorRenderable[]>>;
}

const BlockEditorContext = React.createContext<BlockEditorContextValue | null>(null);

export const BlockEditorProvider = BlockEditorContext.Provider;

export const useBlockEditorContext = () => {
  const ctx = React.useContext(BlockEditorContext);
  if (!ctx) {
    throw new Error('useBlockEditorContext must be used inside BlockEditorProvider');
  }
  return ctx;
};
