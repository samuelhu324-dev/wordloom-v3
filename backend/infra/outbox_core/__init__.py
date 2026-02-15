"""Reusable building blocks for outbox workers.

Intentionally small and projection-agnostic. Individual projections keep their own
outbox tables, but reuse common claim/reclaim/metrics predicates.
"""
