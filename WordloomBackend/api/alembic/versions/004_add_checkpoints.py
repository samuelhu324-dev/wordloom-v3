"""Add checkpoints and markers for note time tracking

Revision ID: 004
Revises: 003
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 orbit_note_checkpoints 表
    op.create_table(
        'orbit_note_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('note_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),  # pending, in_progress, on_hold, done
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),

        # 时间字段
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        # 标签（JSON 存储 tag ID 列表）
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),

        # 外键
        sa.ForeignKeyConstraint(['note_id'], ['orbit_notes.id'], ondelete='CASCADE'),
    )

    op.create_index('idx_checkpoints_note_id', 'orbit_note_checkpoints', ['note_id'])

    # 创建 orbit_note_checkpoint_markers 表
    op.create_table(
        'orbit_note_checkpoint_markers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('checkpoint_id', postgresql.UUID(as_uuid=True), nullable=False),

        # 内容
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),

        # 时间
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='0'),

        # 分类和标签
        sa.Column('category', sa.String(), nullable=False, server_default='work'),  # work, pause, bug, feature, review, custom
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),

        # 显示相关
        sa.Column('color', sa.String(), nullable=False, server_default='#3b82f6'),
        sa.Column('emoji', sa.String(), nullable=False, server_default='✓'),

        # 排序
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        # 外键
        sa.ForeignKeyConstraint(['checkpoint_id'], ['orbit_note_checkpoints.id'], ondelete='CASCADE'),
    )

    op.create_index('idx_markers_checkpoint_id', 'orbit_note_checkpoint_markers', ['checkpoint_id'])


def downgrade() -> None:
    op.drop_index('idx_markers_checkpoint_id', table_name='orbit_note_checkpoint_markers')
    op.drop_table('orbit_note_checkpoint_markers')

    op.drop_index('idx_checkpoints_note_id', table_name='orbit_note_checkpoints')
    op.drop_table('orbit_note_checkpoints')
