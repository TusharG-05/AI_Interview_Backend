"""Add allow_proctoring to InterviewSession

Revision ID: 45a4d943ff0f
Revises: a74b6e9f50ba
Create Date: 2026-04-17 16:34:52.091467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45a4d943ff0f'
down_revision: Union[str, Sequence[str], None] = 'a74b6e9f50ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if column exists first to avoid error on environments where it was manually added
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('interviewsession')]
    if 'allow_proctoring' not in columns:
        op.add_column('interviewsession', sa.Column('allow_proctoring', sa.Boolean(), server_default=sa.text('true'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('interviewsession', 'allow_proctoring')
