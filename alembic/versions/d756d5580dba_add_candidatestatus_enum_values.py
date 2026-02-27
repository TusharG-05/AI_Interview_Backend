"""add_candidatestatus_enum_values

Revision ID: d756d5580dba
Revises: 9a9a2845e9f9
Create Date: 2026-02-27 13:44:12.431210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd756d5580dba'
down_revision: Union[str, Sequence[str], None] = '9a9a2845e9f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
