"""add_allow_copy_paste_to_interviewsession

Revision ID: e1f2a3b4c5d6
Revises: d756d5580dba
Create Date: 2026-03-02

Description:
    Adds a new boolean column `allow_copy_paste` (default False) to the
    `interviewsession` table. This controls whether candidates are permitted
    to copy/paste text during their interview session.

Migration Order:
    1. Apply to Docker DB first: set DATABASE_URL to Docker connection string
       and run: alembic upgrade head
    2. Test all APIs locally.
    3. Apply to NeonDB: update DATABASE_URL to NeonDB connection string
       and run: alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'interviewsession',
        sa.Column(
            'allow_copy_paste',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')
        )
    )


def downgrade() -> None:
    op.drop_column('interviewsession', 'allow_copy_paste')
