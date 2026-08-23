"""create evaluation schema

Revision ID: d4a8e9910f41
Revises: becedf322d72
Create Date: 2026-08-23 12:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4a8e9910f41'
down_revision: Union[str, Sequence[str], None] = 'becedf322d72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'evaluation',
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), nullable=False),
        sa.Column('test_dataset_id', sa.Integer(), nullable=False),
        sa.Column('total_examples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('evaluation_status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('intent_json_validity', sa.Float(), nullable=True),
        sa.Column('intent_structured_accuracy', sa.Float(), nullable=True),
        sa.Column('answer_accuracy', sa.Float(), nullable=True),
        sa.Column('citation_accuracy', sa.Float(), nullable=True),
        sa.Column('policy_flag_accuracy', sa.Float(), nullable=True),
        sa.Column('escalation_accuracy', sa.Float(), nullable=True),
        sa.Column('full_structured_match', sa.Float(), nullable=True),
        sa.Column('normalized_exact_match', sa.Float(), nullable=True),
        sa.Column('critical_safety_failures', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('infrastructure_errors', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('average_latency_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['training_run.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_dataset_id'], ['dataset_version.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('evaluation_id')
    )
    op.create_index(op.f('ix_evaluation_evaluation_id'), 'evaluation', ['evaluation_id'], unique=False)
    op.create_index(op.f('ix_evaluation_run_id'), 'evaluation', ['run_id'], unique=False)
    op.create_index(op.f('ix_evaluation_model_id'), 'evaluation', ['model_id'], unique=False)
    op.create_index(op.f('ix_evaluation_test_dataset_id'), 'evaluation', ['test_dataset_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_evaluation_test_dataset_id'), table_name='evaluation')
    op.drop_index(op.f('ix_evaluation_model_id'), table_name='evaluation')
    op.drop_index(op.f('ix_evaluation_run_id'), table_name='evaluation')
    op.drop_index(op.f('ix_evaluation_evaluation_id'), table_name='evaluation')
    op.drop_table('evaluation')
