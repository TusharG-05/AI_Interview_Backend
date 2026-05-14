"""merge heads

Revision ID: 96d275feaaa1
Revises: 7098ca7308bc, 89e3a9d5f8cd
Create Date: 2026-05-14 10:49:18.254826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96d275feaaa1'
down_revision: Union[str, Sequence[str], None] = ('7098ca7308bc', '89e3a9d5f8cd')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
