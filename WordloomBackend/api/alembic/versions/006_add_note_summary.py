"""Add summary field to orbit_notes

Revision ID: 006
Revises: 005
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 为 orbit_notes 表添加 summary 列
    op.add_column(
        'orbit_notes',
        sa.Column('summary', sa.Text(), nullable=True, server_default='')
    )


def downgrade() -> None:
    # 删除 summary 列
    op.drop_column('orbit_notes', 'summary')
