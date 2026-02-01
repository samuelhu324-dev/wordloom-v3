# ADR-155 Plan173I Basement Library Highlight & Modal Buttons

## Status

Status: Accepted
Date: 2025-12-07
Authors: Frontend Platform Guild (Plan173I)

## Context

1. **Basement library chips still used legacy purple tokens.** Despite the silk-blue palette defined for the Admin area, `BasementMainWidget` highlighted the selected library with a translucent `--accent` overlay that clashed with the updated dashboard screenshot and introduced muddy borders on light monitors.
2. **Restore modal mixed bespoke buttons with shared styles.** The two-mode toggle (原书架 / 选择其他书架) relied on ad-hoc `<button>` tags, so hover/disabled states drifted from the shared Button component and failed our accessibility review (no `aria-pressed`, inconsistent opacity handling).
3. **Documentation lagged behind Plan173 refresh.** `VISUAL_RULES.yaml` still referenced the old accent overlay and did not capture the silk-blue requirement or the modal control migration, creating ambiguity for QA and downstream UI builders.

## Decision

1. **Lock the active library state to the silk-blue token.** `.libraryItemActive` now uses `border-color: var(--color-primary,#2e5e92)`, `background: #f0f6fe (rgb 240/246/254)`, and the shared drop shadow `0 8px 24px rgba(17,34,68,0.12)` so the list matches the Basement hero cards.
2. **Standardize Restore modal controls on `<Button>`.** Original/custom toggle buttons, as well as the primary submit CTA, reuse the shared `Button` (size=`sm`, variant=`primary`) while the cancel action stays a lightweight ghost button; disabled states lower opacity to 0.5 and reflect `aria-pressed` for AT parity.
3. **Update visual rules + ADR trail.** `assets/docs/VISUAL_RULES.yaml` basement section now documents the silk-blue library highlight and the modal button contract so future contributors or QA scripts can assert the correct colors and component usage.

## Consequences

* **Positive:** Basement library selection matches the rest of the Admin palette, reducing visual noise and screenshot drift.
* **Positive:** Shared Button adoption brings instant hover/loading/disabled logic plus consistent ARIA semantics across the Restore flow.
* **Positive:** Documentation + ADR alignment keeps Plan173/174 refresh items auditable for design ops and regression reviews.
* **Negative:** The stronger shadow + saturated border may expose dustier libraries that still rely on inline background colors; follow-up passes must ensure they inherit tokens too.

## Implementation Notes

* CSS: `frontend/src/widgets/basement/BasementMainWidget.module.css` updates `.libraryItemActive` background, border, and shadow.
* Modal: `frontend/src/widgets/RestoreBookModal/index.tsx` swaps bespoke buttons for the shared `Button` component and wires `aria-pressed`/disabled rules.
* Documentation: `assets/docs/VISUAL_RULES.yaml` basement section records the silk-blue list behavior and modal control spec.

## References

* Plan: `assets/docs/QuickLog/D39-55- WordloomDev/archived/Plan_173B_BasementImplementation.md`
* Visual ruleset: `assets/docs/VISUAL_RULES.yaml` (`basement_visual_rules`)
* Code: `frontend/src/widgets/basement/BasementMainWidget.module.css`, `frontend/src/widgets/RestoreBookModal/index.tsx`
