"""Add step tracking columns to training_job

Adds current_step (Integer) and max_steps (Integer) columns to the
training_job table so the real trainer global_step and max_steps values
from state.global_step / state.max_steps are persisted per callback
instead of being estimated in the API layer.

Existing rows receive NULL -- safe, non-destructive.

Revision ID: a9f3c1d2e8b5
Revises: f3a1b2c9d8e7
Create Date: 2026-09-01 16:43:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a9f3c1d2e8b5'
down_revision: Union[str, Sequence[str], None] = 'f3a1b2c9d8e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'training_job',
        sa.Column('current_step', sa.Integer(), nullable=True),
    )
    op.add_column(
        'training_job',
        sa.Column('max_steps', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('training_job', 'max_steps')
    op.drop_column('training_job', 'current_step')
