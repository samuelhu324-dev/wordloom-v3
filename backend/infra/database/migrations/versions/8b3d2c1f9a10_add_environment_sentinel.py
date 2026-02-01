"""Add environment_sentinel table (dev/test safety fuse)

Revision ID: 8b3d2c1f9a10
Revises: 4f2c9a11a8aa
Create Date: 2026-01-30

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b3d2c1f9a10"
down_revision: Union[str, Sequence[str], None] = "4f2c9a11a8aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "environment_sentinel",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("project", sa.Text(), nullable=False),
        sa.Column("env", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Insert a deterministic default based on current database name.
    # This makes the guard work even if you run migrations before inserting metadata manually.
    op.execute(
        """
        INSERT INTO environment_sentinel (id, project, env)
        SELECT 1, 'wordloom',
          CASE
            WHEN current_database() LIKE '%\\_test' THEN 'test'
            WHEN current_database() LIKE '%\\_dev' THEN 'dev'
            ELSE 'sandbox'
          END
        WHERE NOT EXISTS (SELECT 1 FROM environment_sentinel WHERE id = 1)
        """
    )


def downgrade() -> None:
    op.drop_table("environment_sentinel")
