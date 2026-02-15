"""Add search_outbox_events table

Revision ID: 4f2c9a11a8aa
Revises: 3c7b2f1a6d11
Create Date: 2026-01-28

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f2c9a11a8aa"
down_revision: Union[str, Sequence[str], None] = "3c7b2f1a6d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_outbox_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("op", sa.String(length=20), nullable=False),
        sa.Column("event_version", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )

    op.create_index("idx_search_outbox_entity", "search_outbox_events", ["entity_type", "entity_id"], unique=False)
    op.create_index("idx_search_outbox_processed", "search_outbox_events", ["processed_at"], unique=False)
    op.create_index("ix_search_outbox_events_event_version", "search_outbox_events", ["event_version"], unique=False)

    op.alter_column("search_outbox_events", "event_version", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_search_outbox_events_event_version", table_name="search_outbox_events")
    op.drop_index("idx_search_outbox_processed", table_name="search_outbox_events")
    op.drop_index("idx_search_outbox_entity", table_name="search_outbox_events")
    op.drop_table("search_outbox_events")
