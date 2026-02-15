好，那我直接把「UndoManager 给 Copilot 的投喂文案」整理给你，你可以几乎原样丢进去，让它按这个规范写代码。

给 Copilot 的说明（可以直接贴到文件顶部注释）
// Goal:
// Implement a lightweight undo/redo system for the block editor.
// The editor state is a list of Block objects (blocks: Block[]).
// We want Ctrl+Z (undo) and Ctrl+Shift+Z / Ctrl+Y (redo) at the document level.
// No ProseMirror/Slate style transactions, just snapshots for now.

// Requirements:
// 1. Create an UndoManager that lives entirely on the frontend.
//    - It maintains two stacks: undoStack and redoStack.
//    - Each entry is a deep-copied snapshot of the current document state,
//      plus optional selection info.
//
//    interface EditorSnapshot {
//      blocks: Block[];
//      selection?: { blockId: string; offset: number };
//    }
//
// 2. Public API (class or hook is fine):
//    - pushSnapshot(snapshot: EditorSnapshot): void
//      Called after a logical edit (e.g. block text changed, block inserted/deleted,
//      block kind changed). When called:
//        * push current snapshot into undoStack
//        * clear redoStack
//
//    - undo(): EditorSnapshot | null
//      * If undoStack is empty → return null (nothing to do)
//      * Otherwise:
//          - pop one snapshot from undoStack → prev
//          - push current snapshot into redoStack
//          - return prev (caller will load it into React state)
//
//    - redo(): EditorSnapshot | null
//      * If redoStack is empty → return null
//      * Otherwise:
//          - pop one from redoStack → next
//          - push current snapshot into undoStack
//          - return next
//
//    - reset(initialSnapshot: EditorSnapshot): void
//      * Clear both stacks and optionally seed an initial snapshot.
//
// 3. Integration with the editor:
//    - The editor already has a React state like: const [blocks, setBlocks] = ...
//    - We will:
//        * On each "logical operation", call `undoManager.pushSnapshot(currentSnapshot)`
//          BEFORE mutating blocks.
//
//        * Logical operations include:
//            - Enter creates a new block
//            - Backspace merges/deletes blocks
//            - Changing block kind (paragraph/todo/callout/quote/panel)
//            - Reordering blocks
//            - Pasting large text
//        * Typing should be debounced: we will wrap pushSnapshot into a 300ms
//          debounce so multiple keystrokes are grouped as one step.
//
//    - Undo keyboard:
//        * Ctrl+Z / Cmd+Z → undo()
//        * Ctrl+Shift+Z or Ctrl+Y / Cmd+Shift+Z → redo()
//        * These handlers will:
//            - Prevent default browser behavior
//            - Call undoManager.undo() / redo()
//            - If a snapshot is returned, update blocks state and restore selection.
//
// 4. Implementation details:
//    - For deep copy, it's OK to use JSON.parse(JSON.stringify(...)) for now.
//      Document size is small enough.
//    - Undo stack size can be capped (e.g. 100 entries) to avoid memory growth.
//    - Write small helper functions:
//        - createSnapshot(blocks: Block[], selection?: SelectionInfo): EditorSnapshot
//        - cloneSnapshot(snapshot: EditorSnapshot): EditorSnapshot
//
// 5. Non-goals for now:
//    - No need for granular operation-based history.
//    - No need to persist undo/redo across page reloads.
//    - No need to be aware of server sync; this is strictly client-side.
//
// Please implement:
//    - src/editor/undo/UndoManager.ts
// with a default exported class `UndoManager` that satisfies the above API.


你可以先让 Copilot按这个写一个 UndoManager.ts，
之后如果你想，我可以再帮你写一段「在 BlockEditor 里怎么调用 UndoManager + 绑定 Ctrl+Z」的投喂文案。