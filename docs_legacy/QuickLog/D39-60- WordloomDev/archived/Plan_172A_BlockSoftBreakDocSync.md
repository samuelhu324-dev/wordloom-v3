# Plan 172A Block Soft Break Doc Sync

## Goal
Document the Shift+Enter inline soft-break contract that shipped in Plan171A/B so every RULES artifact and ADR reflects the final behavior (inline-only, `\n` persistence, whitespace-aware guards).

## Why
* Code already intercepts `Shift+Enter`, but VISUAL_RULES/DDD_RULES/HEXAGONAL_RULES still describe the older Plan161A helper-only approach.
* QA lacks a single ADR snapshot to reference when auditing regressions.
* Future caret/keyboard plans (173+) need a numbered plan pointing to the documentation debt resolved here.

## Scope & Deliverables
1. **VISUAL_RULES.yaml** — add a Plan171A inline soft-break section that spells out UI interception, text semantics, and QA coverage.
2. **DDD_RULES.yaml** — introduce a DEC05 policy tying `Shift+Enter` to inline editors only, explicitly calling out delete guard/list exit behavior.
3. **HEXAGONAL_RULES.yaml** — record the adapter contract (handlers, helpers, normalization, regression guard) so the Ports & Adapters layer cannot re-route soft breaks.
4. **ADR-151** — new entry under `assets/docs/ADR/` summarizing context/decision/consequences for the inline-only shift+enter design.
5. **Plan172B checklist** — implementation log referencing the precise commits/files once items above land.

## Out of Scope
* Product behavior (already complete in Plan171A/B).
* Additional keyboard shortcuts or spacing changes (captured by future plans if needed).

## Acceptance Criteria
- All three RULES files mention Plan171A inline soft-break guardrails (keyboard interception, `\n` storage, whitespace-empty semantics, QA expectations).
- ADR-151 exists with Accepted status and cross-links to VISUAL/DDD/HEXAGONAL updates.
- QuickLog Plan172B contains verification notes (date, file paths, tests run) referencing this plan.
- No dependency on new migrations or domain fields.

## Dependencies
- Plan_171A_BlockSoftLineBreaking.md
- Plan_171B_Implementation.md
