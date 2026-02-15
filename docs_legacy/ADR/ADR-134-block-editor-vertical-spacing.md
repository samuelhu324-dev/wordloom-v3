# ADR-134 Block Editor Vertical Spacing

## Status

Status: Accepted
Date: 2025-12-02
Authors: Wordloom Editor Team (Plan_143 + Plan_144)

## Context

Legacy BlockRenderer and the new `modules/book-editor` stack were both drawing vertical rhythm from multiple DOM layers: `.list`, `.blockItem`, `.textBlockShell`, UA default margins on `p/ul/li`, and even inline dividers on inner shells. Because every layer added its own margin or padding, collapsing margins produced the “orange gap” captured in Plan143—the visible spacing changed depending on which node the cursor touched, and tweaking one selector just made another default margin take over. The same issue surfaced in the new editor because it reused browser defaults for lists and headings. We needed a single, enforceable source of truth for block-to-block spacing that applies to both stacks and can be audited through DevTools.

## Decision

1. **Single spacing layer (`VERTICAL-01`)**
   - `.blockItem + .blockItem { margin-top: var(--block-gap-md, 0.5rem) }` is the only place allowed to create inter-block distance. Every other DOM layer must keep `margin-top/bottom` at `0` so the focus outline always reflects real spacing.
2. **Internal margin reset (`VERTICAL-02`)**
   - All descendants that previously relied on UA defaults—`p`, `h1~h6`, `ul`, `ol`, `li`, `.textBlockShell`, `.paragraphTextLine`—now get `margin-block: 0`. Dividers move to the block container (`data-divider`) and use padding to keep label-to-rule breathing room (`VERTICAL-03`).
3. **List-specific rhythm (`VERTICAL-04` ~ `VERTICAL-05`)**
   - List indentation lives on `.blockItem ul|ol { padding-left: 1.5rem }`, while the spacing between list items uses `li + li { margin-top: var(--block-list-item-gap, 0.15rem) }`. No list component is allowed to sneak in additional block-level margins.
4. **Kind-aware adjacency tweaks (`VERTICAL-06`)**
   - Special cases (e.g., paragraph followed by list) are implemented via `data-kind` and `data-next-kind` attributes on `.blockItem`, collapsing their adjacent margin to the `gap_tight` token without editing inner markup.
5. **Documentation + debug SOP**
   - VISUAL_RULES.yaml now hosts the authoritative `block_editor_vertical_rhythm` section with VERTICAL-01~06 and the DevTools inspection steps. HEXAGONAL_RULES and DDD_RULES both state that vertical spacing is a UI adapter concern so Domain/Application contracts reject any spacing payloads.

## Consequences

- **Positive:** Designers and QA can adjust global block rhythm by editing a single CSS selector or token instead of hunting for hidden margins across several wrappers.
- **Positive:** Debugging runaway gaps is deterministic—inspect the suspected area, and if the height is not from `.blockItem`, it is automatically an implementation bug.
- **Positive:** Legacy BlockRenderer and the book-editor module stay visually aligned, preventing regression when we phase out the old stack.
- **Neutral:** Every new block plugin must update the VERTICAL margin-reset whitelist; the enforcement cost is acceptable given the clarity it provides.
- **Negative:** Relying on tighter selectors means UA defaults will never help; missing a tag in the reset list leads to obvious regressions, so code reviews must watch for that.

## Implementation Notes

- Key CSS: `frontend/src/features/block/ui/BlockList.module.css`, `frontend/src/modules/book-editor/ui/bookEditor.module.css`.
- Tokens: `--block-gap-md`, `--block-gap-tight`, and `--block-list-item-gap` live at the editor shell; tweak them to tune rhythm without touching components.
- Debug SOP: Use DevTools → Computed → Box Model on the highlighted gap; if the contributing margin/padding/border is not on `.blockItem` or `.blockItemMain`, remove it and add the selector to VERTICAL-02.

## References

- Plan_143_BlockSpacing++.md (QuickLog)
- Plan_144_BlockSpacingManagement.md (QuickLog)
- `assets/docs/VISUAL_RULES.yaml` → `block_editor_vertical_rhythm`
- `assets/docs/HEXAGONAL_RULES.yaml` → `block_editor_vertical_spacing_adapter_policy`
- `assets/docs/DDD_RULES.yaml` → `POLICY-BLOCK-VERTICAL-SPACING-UI-ONLY`
