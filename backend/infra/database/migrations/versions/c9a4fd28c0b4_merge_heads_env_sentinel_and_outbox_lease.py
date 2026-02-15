"""Merge heads: env sentinel + outbox lease

Revision ID: c9a4fd28c0b4
Revises: 8b3d2c1f9a10, b7c0b7a2c2d1
Create Date: 2026-02-01

"""

from typing import Sequence, Union

from alembic import op  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "c9a4fd28c0b4"
down_revision: Union[str, Sequence[str], None] = ("8b3d2c1f9a10", "b7c0b7a2c2d1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge revision (no-op).
    pass


def downgrade() -> None:
    # Merge revision (no-op).
    pass
