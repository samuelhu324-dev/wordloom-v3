# ADR-105 Block Kind Set v2025-11-27 & Comment Model Upgrade

## Status

Status: Proposed
Date: 2025-11-27
Authors: Wordloom Dev (Plan_77)

## Context

The Book workspace now converges Overview / Blocks / Chronicle into a single working surface (ADR-099).  Block editing has evolved from plain text into a richer ecosystem with inline TODOs, media and future plugins.  Plan_77 defines a cleaned-up BlockKind set, an `image_gallery` block for screenshot strips, and a clear separation between "content blocks" and "review comments".

Existing rules (DDD_RULES, HEXAGONAL_RULES, VISUAL_RULES and ADR-080/081/104) still use older naming such as `list_bullet`, `list_numbered`, `list_todo` and treat comments only implicitly via TODO timeline events.  The UI for the Blocks tab (see VISUAL_RULES.book_workspace_tabs_visual_rules) also needs an explicit reference for screenshot strips.

## Decision

1. **BlockKind core set (v2025-11-27)**

   We adopt the following canonical BlockKind enum at the domain/DTO boundary:

   ```ts
   export type BlockKind =
     | 'heading'
     | 'paragraph'
     | 'bulleted_list'
     | 'numbered_list'
     | 'todo_list'
     | 'code'
     | 'callout'
     | 'quote'
     | 'divider'
     | 'image'
     | 'image_gallery'
     | 'custom';
   ```

   - **Text & lists**: `heading`, `paragraph`, `bulleted_list`, `numbered_list`, `todo_list` replace the older `list_*` naming at the API/DTO layer.  The domain enum may continue to use UPPER_SNAKE (HEADING, PARAGRAPH, LIST_BULLET, LIST_NUMBERED, LIST_TODO) as long as adapters perform the mapping.
   - **Engineering blocks**: `code`, `callout`, `quote` keep their existing payload contracts (language/content, variant/text, text/source?).
   - **Structure & media**: `divider` (visual separator) and `image` (single screenshot) become first-class kinds.
   - **Screenshot strip**: `image_gallery` is introduced for 5–8 thumbnail strips / small grids of screenshots, matching the engineering log and UI walkthrough use cases.
   - **Custom**: `custom` remains the reserved experimental container for JSON payloads and prototypes (tables, charts, future plugins).  It must not be used to bypass core kinds.

2. **Block payload contracts (summary)**

   Payload schemas are stabilised as follows (high level, full spec kept in VISUAL_RULES block section):

   - `heading`: `{ level: 1 | 2 | 3; text: RichText }`
   - `paragraph`: `{ text: RichText }`
   - `bulleted_list` / `numbered_list`: `{ items: RichText[] }`
   - `todo_list`: `{ items: { id?: string; text: RichText; status: 'open' | 'done'; isPromoted?: boolean }[] }`
   - `code`: `{ language: string; code: string }`
   - `callout`: `{ variant: 'info' | 'warning' | 'danger' | 'success'; text: RichText }`
   - `quote`: `{ text: RichText; source?: string }`
   - `divider`: `{ style?: 'solid' | 'dashed' } | {}`
   - `image`: `{ imageId: string; url: string; caption?: string }`
   - `image_gallery`: `{ layout: 'strip' | 'grid'; maxPerRow?: number; items: { id: string; url: string; caption?: string; indexLabel?: string }[] }`
   - `custom`: `{ schemaVersion: string; data: unknown }`

   Domain keeps treating `content` as opaque JSON/TEXT.  Validation and rich editing live in the application layer + frontend plugin registry.

3. **Comment model is not a BlockKind**

   - Review comments / discussions are **not** implemented as blocks.
   - Instead, a separate `BlockComment` entity hangs off a Block:

     ```ts
     type BlockComment = {
       id: string;
       bookId: string;
       blockId: string;
       authorId: string;
       content: string;
       createdAt: string;
       resolvedAt?: string | null;
       type?: 'note' | 'issue' | 'suggestion';
     };
     ```

   - Comments support lifecycle (open / resolved), threading and @mention/notification in future phases, and are rendered as side bubbles or a right panel, not as part of the Book content stream.
   - Public annotations that are part of the Book content should use `callout` / `quote` blocks instead.

4. **TODOs stay embedded in Block content**

   - Plan76 remains valid: TODO items live inside the `todo_list` block payload; we **do not** promote Todo to a separate aggregate.
   - Book-level Todo projections (POLICY-BOOK-TODO-PROJECTION and related Chronicle rules) continue to operate on Block content diffs.

5. **Phase & rollout**

   - **Phase 0 (current)**: Backend & frontend accept both legacy `list_bullet/list_numbered/list_todo` and new `bulleted_list/numbered_list/todo_list` at the adapter layer; internal domain enum stays unchanged.  New frontend components must use the new names.
   - **Phase 1**: Once all callers migrated, repository/DTOs and DDD_RULES/HEXAGONAL_RULES/VISUAL_RULES will mark the old names as deprecated aliases.
   - **Phase 2**: Domain enum can optionally be renamed to match the DTO for consistency, coordinated via a migration + release note.

## Consequences

- DDD_RULES gains a single source of truth for BlockKind core set and explicitly records that Comment is *not* a BlockKind.
- HEXAGONAL_RULES clarifies that Block ports treat `content` as opaque JSON, and that comment-related ports live in a separate module (future `comment` or extended `chronicle`/`review`).
- VISUAL_RULES is updated so Block editor / renderer components explicitly support the `image` and `image_gallery` kinds and reserve `custom` for experiments.
- The Book Detail workspace can render screenshot strips using `image_gallery` blocks in the Blocks tab, including future Chronicle evidence views.

## References

- Plan_77_BlockTypes+++.md
- DDD_RULES.yaml POLICY-BLOCK-KIND-CORE-SET, POLICY-BLOCK-TODO-EMBEDDED-MODEL, POLICY-BOOK-TODO-PROJECTION
- HEXAGONAL_RULES.yaml block_editor_hexagonal, todo_projection_strategy
- VISUAL_RULES.yaml block_todo_visual_rules, book_workspace_tabs_visual_rules, book_gallery_visual_rules, media_upload_ui_strategy
- ADR-080-block-editor-integration-rich-block-types-media-plugin-architecture.md
- ADR-081-block-inline-editor-default-removal-overlay-and-component-refactor.md
- ADR-099-book-detail-workspace-tabs-integration.md
- ADR-104-book-todo-block-integration-and-chronicle-timeline-linkage.md
