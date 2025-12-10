# Maturity Module Design

This module isolates all maturity scoring and transition logic away from the `book` aggregate. It follows Plan_98 rules:

- **Domain Layer**: value objects for stages, score breakdowns, snapshot DTOs, plus pure services (`MaturityRuleEngine`) and policies (`MaturityTransitionPolicy`).
- **Application Layer**: input/output DTOs, data provider and repository ports, and use cases for scoring, snapshot persistence, and transition suggestion.
- **Infra Layer Bridges**: adapters in `infra.storage` and `infra.database` to persist `maturity_snapshots`.
- **API Layer**: FastAPI router exposing `/api/v1/maturity/books/{book_id}` endpoints for calculating and retrieving snapshots.

The initial extraction keeps compatibility by leveraging the existing `BookMaturityScoreService` for scoring while presenting new ports for future providers. Persistence is optional: use cases accept a repository that may be `None`, so environments without the new table can still serve read-only calculations.
