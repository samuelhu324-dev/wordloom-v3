# ADR-139 Plan152 Spacing Rollout (Editor + BlockList)

## Status

Status: Accepted
Date: 2025-12-03
Authors: Block Editor / BlockList Working Group (Plan152A + Plan152B)

## Context

Plan149 (ADR-138) standardized block spacing inside the inline editor, but two gaps remained:

1. **BlockList shell + Deleted Blocks Panel** still hard-coded `px` values and bespoke gutter math. QA could not reconcile the “book workspace” screenshots with what `/dev/spacing-test` rendered.
2. **Token visibility** ended at block-level primitives. Designers had no way to inspect BlockList-specific semantics (shell gap, inline gutter, half-step tokens), so reviewing regressions required trawling multiple CSS files.

Plan152A/B set the follow-up goals:

* Extend the Plan149 primitive ladder (`--wl-space-0..6`) with semantic aliases for BlockList shells, inline gutters, todo/pill padding, and panel density.
* Mirror the real BlockList + DeletedBlocksPanel components inside `/app/dev/spacing-test`, exposing live token values so QA can diff the “book workspace” view and the editor view on one screen.
* Update VISUAL_RULES / DDD_RULES / HEXAGONAL_RULES so every stakeholder knows the alias strategy (`--wl-space-section → --wl-space-block-section`, etc.) and the Sandbox requirement before spacing PRs merge.

## Decision

1. **Token matrix expansion**
   * `frontend/src/modules/book-editor/ui/bookEditor.module.css` now declares both primitive tokens (`--wl-space-0..6`, `--wl-space-2-5`, `-3-5`, `-4-5`) and semantic aliases (`--wl-space-block-section`, `--wl-space-block-tight`, bridge tokens for list/todo/quote, todo/list line-height knobs). Legacy `--wl-space-section/tight` stick around as aliases until every surface migrates.
   * `frontend/src/features/block/ui/BlockList.module.css` hosts the BlockList semantics: `--wl-blocklist-shell-gap`, `--wl-blocklist-shell-padding-x/y`, `--wl-blocklist-inline-offset`, `--wl-blocklist-card-gap`, `--wl-blocklist-panel-padding`, `--wl-blocklist-pill-padding-x/y`. DeletedBlocksPanel mirrors the ladder locally for standalone pages but still references the same semantic names.
2. **Spacing Sandbox parity**
   * `/app/dev/spacing-test/page.tsx` now drives two scenario groups. “Editor Rhythm” keeps the Plan149 cards (heading→paragraph, paragraph→list, quote divider, todo stack). “BlockList + Trash Scenarios” renders the real BlockList container and DeletedBlocksPanel via their production CSS modules. QA sees live token badges for each scenario.
   * TOKEN_METADATA splits by scope (`editor` vs `blocklist`) so engineers can read live values for both shells in one snapshot.
3. **Rule synchronization**
   * VISUAL_RULES `block_editor_vertical_rhythm` documents the Plan152 token matrix, alias approach, and sandbox coverage (BlockList cards included).
   * DDD_RULES `POLICY-BLOCK-VERTICAL-SPACING-UI-ONLY` explicitly bans spacing data from Domain payloads, now referencing BlockList/DeletedBlocksPanel shells.
   * HEXAGONAL_RULES `block_editor_vertical_spacing_adapter_policy` ties adapter responsibilities to the new tokens and requires sandbox screenshots for editor + BlockList every time spacing files change.

## Consequences

* **Positive:** Designers and QA read a single “Token Snapshot” grid that covers both the inline editor and BlockList shells. Investigations no longer bounce between multiple routes or screenshots.
* **Positive:** BlockList maintenance inherits the same debounce/alias workflow as the editor—tweaking `--wl-blocklist-card-gap` immediately shows up in the sandbox preview, so no one edits raw `px` values inside React components.
* **Positive:** Documentation drift is reduced: VISUAL/DDD/HEX now name the exact tokens and scopes; PR reviewers can block spacing diffs that skip sandbox updates.
* **Negative:** Any new BlockList-like surface must either reuse the existing semantic tokens or add its own sandbox card plus rule updates before merge, which slightly slows experimentation.

## Implementation Notes

* CSS: `frontend/src/modules/book-editor/ui/bookEditor.module.css`, `frontend/src/features/block/ui/BlockList.module.css`, `frontend/src/features/block/ui/DeletedBlocksPanel.module.css`.
* Sandbox: `frontend/src/app/dev/spacing-test/page.tsx` + `spacingTest.module.css`.
* Docs: `assets/docs/VISUAL_RULES.yaml`, `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`.
* Alias cleanup plan: once no CSS references `--wl-space-section/tight`, drop the alias bridge and update VISUAL_RULES to mark the migration complete.

## References

* QuickLog: `Plan_152A_BlockComplemetations.md`, `Plan_152B_Assessment.md`
* ADR-138 Plan149 spacing reset
* Screens: `/dev/spacing-test` VERTICAL-01~06 badges (Plan152B, Dec 2025)
