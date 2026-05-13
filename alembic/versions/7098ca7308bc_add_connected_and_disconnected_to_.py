"""Add CONNECTED and DISCONNECTED to interviewstatus

Revision ID: 7098ca7308bc
Revises: 8a0d86894eea
Create Date: 2026-05-08 17:17:04.635433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7098ca7308bc'
down_revision: Union[str, Sequence[str], None] = '8a0d86894eea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use autocommit block to allow ALTER TYPE
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE interviewstatus ADD VALUE 'CONNECTED'")
        op.execute("ALTER TYPE interviewstatus ADD VALUE 'DISCONNECTED'")

def downgrade() -> None:
    # Note: PostgreSQL does not support removing values from an ENUM type easily.
    # Usually, you would have to recreate the type, which is complex and risky.
    # For status enums, it's generally fine to leave the values in the DB.
    pass
