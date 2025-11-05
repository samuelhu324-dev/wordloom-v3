"""Add pinned fields to bookshelves and notes

Revision ID: 003
Revises: 002
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_pinned and pinned_at to orbit_bookshelves
    op.add_column('orbit_bookshelves', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('orbit_bookshelves', sa.Column('pinned_at', sa.DateTime(timezone=True), nullable=True))

    # Add is_pinned and pinned_at to orbit_notes
    op.add_column('orbit_notes', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('orbit_notes', sa.Column('pinned_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove columns from orbit_notes
    op.drop_column('orbit_notes', 'pinned_at')
    op.drop_column('orbit_notes', 'is_pinned')

    # Remove columns from orbit_bookshelves
    op.drop_column('orbit_bookshelves', 'pinned_at')
    op.drop_column('orbit_bookshelves', 'is_pinned')
