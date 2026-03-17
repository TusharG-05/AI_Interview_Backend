"""Merge conflicting heads

Revision ID: b00191284125
Revises: 07cdb601f358, 8359b2c76beb
Create Date: 2026-03-17 12:35:58.068703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b00191284125'
down_revision: Union[str, Sequence[str], None] = ('07cdb601f358', '8359b2c76beb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
