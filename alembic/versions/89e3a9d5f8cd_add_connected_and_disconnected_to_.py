"""add_connected_and_disconnected_to_interviewstatus

Revision ID: 89e3a9d5f8cd
Revises: 8a0d86894eea
Create Date: 2026-05-08 17:21:13.613161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89e3a9d5f8cd'
down_revision: Union[str, Sequence[str], None] = '8a0d86894eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
