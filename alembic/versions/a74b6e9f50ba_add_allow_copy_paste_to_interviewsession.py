"""Add allow_copy_paste to InterviewSession

Revision ID: a74b6e9f50ba
Revises: c2f677208028
Create Date: 2026-03-23 13:55:34.877342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a74b6e9f50ba'
down_revision: Union[str, Sequence[str], None] = 'c2f677208028'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('interviewsession', sa.Column('allow_copy_paste', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('interviewsession', 'allow_copy_paste')
