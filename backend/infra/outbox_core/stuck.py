from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import ColumnElement


def stuck_processing_predicate(
    model: object,
    *,
    now: datetime,
    max_processing_seconds: int,
) -> ColumnElement[bool]:
    """SQL predicate for rows that are 'stuck' in processing.

    A row is stuck if:
    - it is still unprocessed
    - status == 'processing'
    - AND either:
      - lease_until has expired, OR
      - processing_started_at is older than now - max_processing_seconds

    The model is expected to look like SearchOutboxEventModel (attributes used).
    """

    max_age_started_at = now - timedelta(seconds=max(1, int(max_processing_seconds)))

    processed_at = getattr(model, "processed_at")
    status = getattr(model, "status")
    lease_until = getattr(model, "lease_until")
    processing_started_at = getattr(model, "processing_started_at")

    return and_(
        processed_at.is_(None),
        status == "processing",
        or_(
            and_(lease_until.is_not(None), lease_until < now),
            and_(processing_started_at.is_not(None), processing_started_at < max_age_started_at),
        ),
    )
