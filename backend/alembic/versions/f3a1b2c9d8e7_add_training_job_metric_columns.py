"""Add real-time metric columns to training_job table

Adds train_loss (Float), current_lr (Float), and log_entries (Text/JSON)
columns to persist actual SFTTrainer step metrics into Neon PostgreSQL.
Existing rows receive NULL for all new columns -- safe, non-destructive.

Revision ID: f3a1b2c9d8e7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-01 08:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1b2c9d8e7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add real-time metric columns to training_job."""
    op.add_column(
        'training_job',
        sa.Column('train_loss', sa.Float(), nullable=True)
    )
    op.add_column(
        'training_job',
        sa.Column('current_lr', sa.Float(), nullable=True)
    )
    op.add_column(
        'training_job',
        sa.Column('log_entries', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Remove real-time metric columns from training_job."""
    op.drop_column('training_job', 'log_entries')
    op.drop_column('training_job', 'current_lr')
    op.drop_column('training_job', 'train_loss')
