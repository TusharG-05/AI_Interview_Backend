"""Cascade delete users - Replace sentinel system with ON DELETE CASCADE

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7, bb04cbdbc713
Create Date: 2026-02-26 10:30:00.000000

Changes:
- InterviewSession: Make admin_id and candidate_id NULLABLE
- InterviewSession: Add ON DELETE CASCADE to admin_id and candidate_id FKs
- Remove sentinel placeholder users from the database
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = ('b2c3d4e5f6a7', 'bb04cbdbc713')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADMIN_DELETED_EMAIL = "__admin_deleted__@system"
CANDIDATE_DELETED_EMAIL = "__candidate_deleted__@system"


def upgrade() -> None:
    conn = op.get_bind()

    # ---- 1. Make columns nullable and add ON DELETE CASCADE ----
    with op.batch_alter_table('interviewsession', schema=None) as batch_op:
        # Drop existing FK constraints and recreate with CASCADE
        batch_op.drop_constraint('interviewsession_admin_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('interviewsession_candidate_id_fkey', type_='foreignkey')

        batch_op.alter_column('admin_id',
            existing_type=sa.Integer(),
            nullable=True
        )
        batch_op.alter_column('candidate_id',
            existing_type=sa.Integer(),
            nullable=True
        )

        batch_op.create_foreign_key(
            'interviewsession_admin_id_fkey',
            'user', ['admin_id'], ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'interviewsession_candidate_id_fkey',
            'user', ['candidate_id'], ['id'],
            ondelete='CASCADE'
        )

    # ---- 2. Revert sentinel references back to NULL ----
    admin_row = conn.execute(
        sa.text('SELECT id FROM "user" WHERE email = :email'),
        {"email": ADMIN_DELETED_EMAIL}
    ).first()
    candidate_row = conn.execute(
        sa.text('SELECT id FROM "user" WHERE email = :email'),
        {"email": CANDIDATE_DELETED_EMAIL}
    ).first()

    if admin_row:
        conn.execute(
            sa.text('UPDATE interviewsession SET admin_id = NULL WHERE admin_id = :sid'),
            {"sid": admin_row[0]}
        )
    if candidate_row:
        conn.execute(
            sa.text('UPDATE interviewsession SET candidate_id = NULL WHERE candidate_id = :sid'),
            {"sid": candidate_row[0]}
        )

    # ---- 3. Delete sentinel users ----
    conn.execute(
        sa.text('DELETE FROM "user" WHERE email IN (:e1, :e2)'),
        {"e1": ADMIN_DELETED_EMAIL, "e2": CANDIDATE_DELETED_EMAIL}
    )


def downgrade() -> None:
    """Downgrade: restore nullable columns without CASCADE (no sentinel recreation)."""
    with op.batch_alter_table('interviewsession', schema=None) as batch_op:
        batch_op.drop_constraint('interviewsession_admin_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('interviewsession_candidate_id_fkey', type_='foreignkey')

        batch_op.create_foreign_key(
            'interviewsession_admin_id_fkey',
            'user', ['admin_id'], ['id']
        )
        batch_op.create_foreign_key(
            'interviewsession_candidate_id_fkey',
            'user', ['candidate_id'], ['id']
        )
