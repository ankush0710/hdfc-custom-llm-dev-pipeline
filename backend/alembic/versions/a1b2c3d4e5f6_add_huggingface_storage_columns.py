
"""add huggingface storage columns

Revision ID: a1b2c3d4e5f6
Revises: f9b1c2d3e4f5
Create Date: 2026-08-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f9b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to include Hugging Face storage metadata columns."""
    # Add Hugging Face columns to dataset_version
    op.add_column('dataset_version', sa.Column('huggingface_repo', sa.String(length=255), nullable=True))
    op.add_column('dataset_version', sa.Column('huggingface_path', sa.String(length=500), nullable=True))
    op.add_column('dataset_version', sa.Column('commit_hash', sa.String(length=128), nullable=True))

    # Add Hugging Face columns and model_size to model_registry
    op.add_column('model_registry', sa.Column('huggingface_repo', sa.String(length=255), nullable=True))
    op.add_column('model_registry', sa.Column('huggingface_path', sa.String(length=500), nullable=True))
    op.add_column('model_registry', sa.Column('commit_hash', sa.String(length=128), nullable=True))
    op.add_column('model_registry', sa.Column('model_size', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('model_registry', 'model_size')
    op.drop_column('model_registry', 'commit_hash')
    op.drop_column('model_registry', 'huggingface_path')
    op.drop_column('model_registry', 'huggingface_repo')

    op.drop_column('dataset_version', 'commit_hash')
    op.drop_column('dataset_version', 'huggingface_path')
    op.drop_column('dataset_version', 'huggingface_repo')
