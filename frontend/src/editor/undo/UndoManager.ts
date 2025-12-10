/**
 * Goal:
 * Implement a lightweight undo/redo system for the block editor.
 * The editor state is a list of Block objects (blocks: Block[]).
 * We want Ctrl+Z (undo) and Ctrl+Shift+Z / Ctrl+Y (redo) at the document level.
 * No ProseMirror/Slate style transactions, just snapshots for now.
 */

import type { BlockDto } from '@/entities/block';

export interface SelectionInfo {
  blockId: string;
  offset: number;
}

export interface EditorSnapshot {
  blocks: BlockDto[];
  selection?: SelectionInfo;
}

const MAX_STACK_SIZE = 100;

const deepClone = <T>(value: T): T => JSON.parse(JSON.stringify(value));

export const createSnapshot = (blocks: BlockDto[], selection?: SelectionInfo): EditorSnapshot => ({
  blocks: deepClone(blocks),
  selection: selection ? { ...selection } : undefined,
});

export const cloneSnapshot = (snapshot: EditorSnapshot): EditorSnapshot => ({
  blocks: deepClone(snapshot.blocks),
  selection: snapshot.selection ? { ...snapshot.selection } : undefined,
});

export default class UndoManager {
  private undoStack: EditorSnapshot[] = [];

  private redoStack: EditorSnapshot[] = [];

  private currentSnapshot: EditorSnapshot | null = null;

  constructor(private readonly capacity: number = MAX_STACK_SIZE) {}

  pushSnapshot(snapshot: EditorSnapshot): void {
    const cloned = cloneSnapshot(snapshot);
    if (this.currentSnapshot) {
      this.undoStack.push(cloneSnapshot(this.currentSnapshot));
      this.trimStack(this.undoStack);
    }
    this.currentSnapshot = cloned;
    this.redoStack = [];
  }

  undo(): EditorSnapshot | null {
    if (this.undoStack.length === 0 || !this.currentSnapshot) {
      return null;
    }
    const previous = this.undoStack.pop()!;
    this.redoStack.push(cloneSnapshot(this.currentSnapshot));
    this.trimStack(this.redoStack);
    this.currentSnapshot = cloneSnapshot(previous);
    return cloneSnapshot(previous);
  }

  redo(): EditorSnapshot | null {
    if (this.redoStack.length === 0 || !this.currentSnapshot) {
      return null;
    }
    const next = this.redoStack.pop()!;
    this.undoStack.push(cloneSnapshot(this.currentSnapshot));
    this.trimStack(this.undoStack);
    this.currentSnapshot = cloneSnapshot(next);
    return cloneSnapshot(next);
  }

  reset(initialSnapshot?: EditorSnapshot): void {
    this.undoStack = [];
    this.redoStack = [];
    this.currentSnapshot = initialSnapshot ? cloneSnapshot(initialSnapshot) : null;
  }

  getCurrentSnapshot(): EditorSnapshot | null {
    return this.currentSnapshot ? cloneSnapshot(this.currentSnapshot) : null;
  }

  private trimStack(stack: EditorSnapshot[]): void {
    while (stack.length > this.capacity) {
      stack.shift();
    }
  }
}
