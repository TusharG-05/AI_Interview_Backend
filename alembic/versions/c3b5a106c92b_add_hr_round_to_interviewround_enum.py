"""add HR_ROUND to InterviewRound enum

Revision ID: c3b5a106c92b
Revises: 719ea964e694
Create Date: 2026-06-10 17:14:06.760129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3b5a106c92b'
down_revision: Union[str, Sequence[str], None] = '719ea964e694'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE interviewround ADD VALUE IF NOT EXISTS 'HR_ROUND'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
