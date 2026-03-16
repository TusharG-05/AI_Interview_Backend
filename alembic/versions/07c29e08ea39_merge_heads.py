"""merge_heads

Revision ID: 07c29e08ea39
Revises: 0fe0fcfa0662, 1d08d1c452cc, g1h2i3j4k5l6
Create Date: 2026-03-13 10:19:38.272238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07c29e08ea39'
down_revision: Union[str, Sequence[str], None] = '1d08d1c452cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
