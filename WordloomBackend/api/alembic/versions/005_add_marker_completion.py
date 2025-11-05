"""Add is_completed field to checkpoint markers

Revision ID: 005
Revises: 004
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 为 orbit_note_checkpoint_markers 表添加 is_completed 列
    op.add_column(
        'orbit_note_checkpoint_markers',
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    # 删除 is_completed 列
    op.drop_column('orbit_note_checkpoint_markers', 'is_completed')
