"""merge heads

Revision ID: fc30b3cdf0c7
Revises: f1a2b3c4d5e6, ce0f6c6b6e65
Create Date: 2026-03-11 14:13:06.275326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc30b3cdf0c7'
down_revision: Union[str, Sequence[str], None] = ('f1a2b3c4d5e6', 'ce0f6c6b6e65')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
