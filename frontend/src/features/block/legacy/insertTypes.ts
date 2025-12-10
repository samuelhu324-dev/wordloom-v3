import { BlockKind } from '@/entities/block';

// LEGACY: Types for the deprecated BlockList insert flows.

export type BlockInsertPosition = 'before' | 'after';
export type BlockInsertSource = 'bottom-menu' | 'inline-plus' | 'slash-command' | 'enter-key';

export interface BlockInsertOptions {
  anchorBlockId?: string;
  position?: BlockInsertPosition;
  source?: BlockInsertSource;
  headingLevel?: 1 | 2 | 3;
}

export type InsertBlockHandler = (
  position: BlockInsertPosition,
  kind: BlockKind,
  source: BlockInsertSource,
  options?: BlockInsertOptions
) => void;
