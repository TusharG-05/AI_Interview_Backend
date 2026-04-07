"""merge multiple heads

Revision ID: 07cdb601f358
Revises: 74d2b17f9873, db5a6730bf74
Create Date: 2026-03-16 17:13:03.392917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07cdb601f358'
down_revision: Union[str, Sequence[str], None] = ('74d2b17f9873', 'db5a6730bf74')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
