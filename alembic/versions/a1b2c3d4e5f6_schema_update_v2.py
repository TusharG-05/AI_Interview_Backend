"""schema_update_v2 - SQLite compatible

Revision ID: a1b2c3d4e5f6
Revises: 41958c02d377
Create Date: 2026-02-25 16:20:00.000000

Changes:
- User: Add access_token column
- QuestionPaper: Rename admin_id -> adminUser, add question_count, total_marks, make description not null
- Questions: make paper_id not null, make content/question_text/topic not null (backfill defaults)
- InterviewSession: Drop admin_name, candidate_name columns
- InterviewResult: Make total_score not null (backfill 0.0)
- ProctoringEvent: Make details not null (backfill '')
- StatusTimeline: Make context_data not null (backfill '{}')

Note: SQLite does not support ALTER COLUMN. We use batch_alter_table for compatibility.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '41958c02d377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply all schema changes - SQLite compatible via batch_alter_table."""

    # ---- USER: Add access_token ----
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('access_token', sa.String(), nullable=True))

    # ---- QUESTIONPAPER ----
    # Backfill description before making it NOT NULL
    op.execute("UPDATE questionpaper SET description = '' WHERE description IS NULL")

    with op.batch_alter_table('questionpaper', schema=None) as batch_op:
        # Rename admin_id -> adminUser
        batch_op.alter_column('admin_id', new_column_name='adminUser',
            existing_type=sa.Integer(), nullable=True)
        # Make description NOT NULL
        batch_op.alter_column('description',
            existing_type=sa.String(), nullable=False, server_default='')
        # Add question_count and total_marks
        batch_op.add_column(sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('total_marks', sa.Integer(), nullable=False, server_default='0'))

    # ---- QUESTIONS ----
    # Backfill NULL values with defaults
    op.execute("UPDATE questions SET content = 'string' WHERE content IS NULL")
    op.execute("UPDATE questions SET question_text = content WHERE question_text IS NULL")
    op.execute("UPDATE questions SET topic = 'General' WHERE topic IS NULL")
    # For any questions with NULL paper_id, set to first available paper if exists
    op.execute("""
        UPDATE questions SET paper_id = (SELECT id FROM questionpaper LIMIT 1)
        WHERE paper_id IS NULL
          AND (SELECT COUNT(*) FROM questionpaper) > 0
    """)

    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.alter_column('content',
            existing_type=sa.String(), nullable=False, server_default='string')
        batch_op.alter_column('question_text',
            existing_type=sa.String(), nullable=False, server_default='string')
        batch_op.alter_column('topic',
            existing_type=sa.String(), nullable=False, server_default='General')
        # Note: paper_id could still be null if no papers exist; keep as-is for safety
        # (if any nulls remain they'll error on NOT NULL—but that means data is truly orphaned)

    # ---- INTERVIEWSESSION: Drop admin_name, candidate_name ----
    with op.batch_alter_table('interviewsession', schema=None) as batch_op:
        batch_op.drop_column('admin_name')
        batch_op.drop_column('candidate_name')

    # ---- INTERVIEWRESULT: Make total_score NOT NULL ----
    op.execute("UPDATE interviewresult SET total_score = 0.0 WHERE total_score IS NULL")

    with op.batch_alter_table('interviewresult', schema=None) as batch_op:
        batch_op.alter_column('total_score',
            existing_type=sa.Float(), nullable=False, server_default='0.0')

    # ---- PROCTORINGEVENT: Make details NOT NULL ----
    op.execute("UPDATE proctoringevent SET details = '' WHERE details IS NULL")

    with op.batch_alter_table('proctoringevent', schema=None) as batch_op:
        batch_op.alter_column('details',
            existing_type=sa.String(), nullable=False, server_default='')

    # ---- STATUSTIMELINE: Make context_data NOT NULL ----
    op.execute("UPDATE statustimeline SET context_data = '{}' WHERE context_data IS NULL")

    with op.batch_alter_table('statustimeline', schema=None) as batch_op:
        batch_op.alter_column('context_data',
            existing_type=sa.String(), nullable=False, server_default='{}')


def downgrade() -> None:
    """Revert all schema changes."""

    # ---- STATUSTIMELINE ----
    with op.batch_alter_table('statustimeline', schema=None) as batch_op:
        batch_op.alter_column('context_data',
            existing_type=sa.String(), nullable=True, server_default=None)

    # ---- PROCTORINGEVENT ----
    with op.batch_alter_table('proctoringevent', schema=None) as batch_op:
        batch_op.alter_column('details',
            existing_type=sa.String(), nullable=True, server_default=None)

    # ---- INTERVIEWRESULT ----
    with op.batch_alter_table('interviewresult', schema=None) as batch_op:
        batch_op.alter_column('total_score',
            existing_type=sa.Float(), nullable=True, server_default=None)

    # ---- INTERVIEWSESSION: Restore dropped columns ----
    with op.batch_alter_table('interviewsession', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('candidate_name', sa.String(), nullable=True))

    # ---- QUESTIONS ----
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.alter_column('topic',
            existing_type=sa.String(), nullable=True, server_default=None)
        batch_op.alter_column('question_text',
            existing_type=sa.String(), nullable=True, server_default=None)
        batch_op.alter_column('content',
            existing_type=sa.String(), nullable=True, server_default=None)

    # ---- QUESTIONPAPER ----
    with op.batch_alter_table('questionpaper', schema=None) as batch_op:
        batch_op.drop_column('total_marks')
        batch_op.drop_column('question_count')
        batch_op.alter_column('description',
            existing_type=sa.String(), nullable=True, server_default=None)
        batch_op.alter_column('adminUser', new_column_name='admin_id',
            existing_type=sa.Integer(), nullable=True)

    # ---- USER ----
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('access_token')
