# ADR-108 Plan77 BlockKind Roadmap and Renderer Stack

## Status

Status: Accepted
Date: 2025-11-27
Authors: Wordloom Dev (Plan_77)

## Context

The Blocks tab previously rendered one textarea per record and treated `content` as an opaque string. Plan_77 defines the long-term roadmap for Block kinds (heading, paragraph, lists, todo, code, media, etc.) and mandates a renderer/editor split that can evolve without rewriting the data model. We already landed Plan80/Plan82 (inline paper + single-block editing) and introduced typed DTO helpers, but there was no canonical document explaining:

- How BlockKind is represented across domain, adapters, and UI.
- How to keep the backend/API contract stable while we add structured payloads.
- How the renderer stack will introduce new kinds phase-by-phase without breaking existing flows.
- How Plan_77 aligns VISUAL/HEXAGONAL/DDD rules so future contributors do not regress to free-form strings or card-based UIs.

## Decision

1. **BlockKind-aware DTO contract (Phase v1 foundation)**
   - Block.kind is now mandatory across domain/entity/DTO layers and must be one of the canonical kinds enumerated in Plan_77; paragraph is the only permitted creation target during Phase v1.
   - Block.content is persisted as JSON (`{"text": string}` for paragraph). Repository adapters must coerce legacy strings into the structured shape before returning them to application services.
   - `fractional_index` supersedes the legacy `order` column; adapters fill the field for clients even if a migration still stores `order`, ensuring future reordering work can rely on fractional math.

2. **Adapter mapping rules**
   - REST responses include both `type` (legacy) and `kind`; adapters (frontend `normalizeBlock`, backend DTO serializers) must map between the two via shared utilities (`mapApiTypeToKind`, `mapKindToApiType`).
   - `parseBlockContent(kind, raw)` is the single point that converts JSON strings into the `BlockContent` union; UI components never operate on raw strings again.
   - Create/Update requests accept `kind` + `content` (string for now). Application services are responsible for wrapping paragraph text into `{text}` before persistence and for rejecting content that does not match the declared kind. Shared helpers (`createDefaultBlockContent`, `serializeBlockContent`) ensure insert menus and overview widgets do not drift from backend expectations.

3. **Renderer stack**
   - `BlockRenderer` orchestrates reading/editing states and delegates to `BlockDisplay` and `BlockEditor`. In Phase v1 it only renders `ParagraphDisplay` / `ParagraphEditor`, but the switch statement is mandatory scaffolding for upcoming kinds.
   - BlockList/InlineCreateBar interact exclusively with `BlockRenderer`, keeping Plan80/Plan82 behaviors (hover toolbar, SaveAll handle, Ctrl/Cmd+S) unchanged while insulating future kind-specific UIs.
   - Unsupported kinds render a placeholder stub so backend experiments cannot crash the page; proper support requires a follow-up PR plus RULES/ADR updates.

4. **Phased rollout roadmap**
   - **Phase v1 (delivered Nov 27, 2025):** paragraph-only blocks, structured DTOs, renderer stack, documentation in VISUAL/HEXAGONAL/DDD.
   - **Phase v1.5:** add `heading`, `bulleted_list`, `numbered_list`. Each kind gets a minimal display/editor (single-line textarea for headings, multi-line list textarea) but reuses BlockRenderer plumbing.
   - **Phase v2 (delivered Nov 27, 2025 via Plan83):** introduce `todo_list`, `callout`, `quote`, `divider`, `image`, `image_gallery`, `custom`. This phase requires new UI widgets (checkbox matrix, media pickers) plus backend schema validators; each addition must extend the enums, DTO helpers, RULES files, and this ADR.
   - Every phase must remain backward compatible via adapters; migrations can be staged independently of UI releases as long as the contract above holds.

## Consequences

- Frontend code now consumes structured Block DTOs, unlocking richer renderers without touching the API each time.
- Backend services gain a clear checklist before introducing new kinds (enum update, schema validation, RULES sync, renderer case).
- QA/regression scope becomes phase-based: v1 testing focuses on paragraph behavior; v1.5+ adds targeted cases per new kind.
- Future contributors have a canonical reference linking Plan_77, the renderer stack, and RULES updates, reducing tribal knowledge.

## References

- assets/docs/QuickLog/D39-45- WordloomDev/archived/Plan_77_BlockTypes+++.md
- assets/docs/VISUAL_RULES.yaml (`block_renderer_plan77_v1`)
- assets/docs/HEXAGONAL_RULES.yaml (`block_renderer_plan77_adapter`)
- assets/docs/DDD_RULES.yaml (`POLICY-BLOCK-PLAN77-V1-CONTENT`, `POLICY-BLOCK-PLAN77-DTO-ADAPTER`)
- frontend/src/entities/block/types.ts
- frontend/src/features/block/model/api.ts
- frontend/src/features/block/ui/BlockRenderer.tsx
