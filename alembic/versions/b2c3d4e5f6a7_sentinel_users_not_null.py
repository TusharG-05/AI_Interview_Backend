"""schema_update_v3 - Enforce NOT NULL on admin_id and candidate_id via sentinel users

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-25 16:48:00.000000

Changes:
- InterviewSession: Make admin_id and candidate_id NOT NULL
  - First inserts sentinel users "__admin_deleted__@system" and "__candidate_deleted__@system"
  - Updates any existing NULLs to point to those sentinel users
  - Then applies NOT NULL constraint
- QuestionPaper: adminUser (formerly admin_id) is kept nullable (orphaned papers is acceptable)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADMIN_DELETED_EMAIL = "__admin_deleted__@system"
CANDIDATE_DELETED_EMAIL = "__candidate_deleted__@system"


def upgrade() -> None:
    conn = op.get_bind()

    # ---- 1. Create sentinel users if they don't exist ----
    admin_row = conn.execute(
        sa.text("SELECT id FROM user WHERE email = :email"),
        {"email": ADMIN_DELETED_EMAIL}
    ).first()

    if not admin_row:
        conn.execute(
            sa.text(
                "INSERT INTO user (email, full_name, password_hash, role) "
                "VALUES (:email, :full_name, :password_hash, :role)"
            ),
            {
                "email": ADMIN_DELETED_EMAIL,
                "full_name": "Deleted Admin",
                "password_hash": "__sentinel__",
                "role": "admin"
            }
        )
        admin_row = conn.execute(
            sa.text("SELECT id FROM user WHERE email = :email"),
            {"email": ADMIN_DELETED_EMAIL}
        ).first()

    candidate_row = conn.execute(
        sa.text("SELECT id FROM user WHERE email = :email"),
        {"email": CANDIDATE_DELETED_EMAIL}
    ).first()

    if not candidate_row:
        conn.execute(
            sa.text(
                "INSERT INTO user (email, full_name, password_hash, role) "
                "VALUES (:email, :full_name, :password_hash, :role)"
            ),
            {
                "email": CANDIDATE_DELETED_EMAIL,
                "full_name": "Deleted Candidate",
                "password_hash": "__sentinel__",
                "role": "candidate"
            }
        )
        candidate_row = conn.execute(
            sa.text("SELECT id FROM user WHERE email = :email"),
            {"email": CANDIDATE_DELETED_EMAIL}
        ).first()

    admin_sentinel_id = admin_row[0]
    candidate_sentinel_id = candidate_row[0]

    # ---- 2. Backfill NULL admin_id -> sentinel admin ----
    conn.execute(
        sa.text("UPDATE interviewsession SET admin_id = :sid WHERE admin_id IS NULL"),
        {"sid": admin_sentinel_id}
    )

    # ---- 3. Backfill NULL candidate_id -> sentinel candidate ----
    conn.execute(
        sa.text("UPDATE interviewsession SET candidate_id = :sid WHERE candidate_id IS NULL"),
        {"sid": candidate_sentinel_id}
    )

    # ---- 4. Make admin_id and candidate_id NOT NULL ----
    with op.batch_alter_table('interviewsession', schema=None) as batch_op:
        batch_op.alter_column('admin_id',
            existing_type=sa.Integer(),
            nullable=False
        )
        batch_op.alter_column('candidate_id',
            existing_type=sa.Integer(),
            nullable=False
        )


def downgrade() -> None:
    with op.batch_alter_table('interviewsession', schema=None) as batch_op:
        batch_op.alter_column('admin_id',
            existing_type=sa.Integer(),
            nullable=True
        )
        batch_op.alter_column('candidate_id',
            existing_type=sa.Integer(),
            nullable=True
        )

    conn = op.get_bind()

    # Revert sentinels back to NULL (reverse of upgrade)
    admin_row = conn.execute(
        sa.text("SELECT id FROM user WHERE email = :email"),
        {"email": ADMIN_DELETED_EMAIL}
    ).first()
    candidate_row = conn.execute(
        sa.text("SELECT id FROM user WHERE email = :email"),
        {"email": CANDIDATE_DELETED_EMAIL}
    ).first()

    if admin_row:
        conn.execute(
            sa.text("UPDATE interviewsession SET admin_id = NULL WHERE admin_id = :sid"),
            {"sid": admin_row[0]}
        )
    if candidate_row:
        conn.execute(
            sa.text("UPDATE interviewsession SET candidate_id = NULL WHERE candidate_id = :sid"),
            {"sid": candidate_row[0]}
        )
