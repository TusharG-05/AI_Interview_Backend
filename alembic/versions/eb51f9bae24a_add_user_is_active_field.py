"""add_user_is_active_field

Revision ID: eb51f9bae24a
Revises: 1aab88f7e124
Create Date: 2026-02-06 12:09:51.134039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb51f9bae24a'
down_revision: Union[str, Sequence[str], None] = '1aab88f7e124'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
