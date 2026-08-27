"""add pii and training safety fields

Revision ID: f9b1c2d3e4f5
Revises: c4a27aec5943
Create Date: 2026-08-27 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9b1c2d3e4f5'
down_revision: Union[str, Sequence[str], None] = 'c4a27aec5943'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include PII detection and training safety fields."""
    # Add columns to dataset_version
    op.add_column('dataset_version', sa.Column('is_safe_for_training', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('dataset_version', sa.Column('pii_scan_status', sa.String(length=50), server_default='PENDING', nullable=False))

    # Add columns to quality_metrics
    op.add_column('quality_metrics', sa.Column('pii_instances_detected', sa.Integer(), server_default='0', nullable=True))
    op.add_column('quality_metrics', sa.Column('pii_types_detected', sa.String(length=500), server_default='NONE', nullable=True))
    op.add_column('quality_metrics', sa.Column('records_sanitized', sa.Integer(), server_default='0', nullable=True))
    op.add_column('quality_metrics', sa.Column('is_safe_for_training', sa.Boolean(), server_default='false', nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('quality_metrics', 'is_safe_for_training')
    op.drop_column('quality_metrics', 'records_sanitized')
    op.drop_column('quality_metrics', 'pii_types_detected')
    op.drop_column('quality_metrics', 'pii_instances_detected')

    op.drop_column('dataset_version', 'pii_scan_status')
    op.drop_column('dataset_version', 'is_safe_for_training')
