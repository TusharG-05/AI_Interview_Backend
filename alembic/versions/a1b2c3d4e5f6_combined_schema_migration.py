"""combined_schema_migration

Combines two migrations:
- 4594ffb8803c (apply_dbml_schema_strict_validation)
- 7437a699d68c (remove_candidate_name_admin_name)

Revision ID: a1b2c3d4e5f6
Revises: bb04cbdbc713
Create Date: 2026-02-26 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'bb04cbdbc713'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Part 1: Strict validation (from 4594ffb8803c) ---
    
    # Backfill missing values to prevent NotNullViolation on existing rows
    op.execute("UPDATE answers SET candidate_answer = '' WHERE candidate_answer IS NULL")
    op.execute("UPDATE answers SET feedback = '' WHERE feedback IS NULL")
    op.execute("UPDATE answers SET score = 0.0 WHERE score IS NULL")
    op.execute("UPDATE answers SET audio_path = '' WHERE audio_path IS NULL")
    op.execute("UPDATE answers SET transcribed_text = '' WHERE transcribed_text IS NULL")
    op.execute("UPDATE interviewresult SET total_score = 0.0 WHERE total_score IS NULL")
    op.execute("UPDATE interviewsession SET max_questions = 0 WHERE max_questions IS NULL")
    op.execute("UPDATE interviewsession SET current_status = 'INVITED' WHERE current_status IS NULL")
    op.execute("UPDATE interviewsession SET last_activity = CURRENT_TIMESTAMP WHERE last_activity IS NULL")
    op.execute("UPDATE proctoringevent SET details = '' WHERE details IS NULL")
    op.execute("UPDATE questionpaper SET description = '' WHERE description IS NULL")
    op.execute("UPDATE questions SET content = '' WHERE content IS NULL")
    op.execute("UPDATE questions SET question_text = '' WHERE question_text IS NULL")
    op.execute("UPDATE questions SET topic = '' WHERE topic IS NULL")
    op.execute("UPDATE statustimeline SET context_data = '' WHERE context_data IS NULL")
    
    # answers: enforce NOT NULL
    op.alter_column('answers', 'candidate_answer', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('answers', 'feedback', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('answers', 'score', existing_type=sa.DOUBLE_PRECISION(precision=53), nullable=False)
    op.alter_column('answers', 'audio_path', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('answers', 'transcribed_text', existing_type=sa.VARCHAR(), nullable=False)
    
    # interviewresult: enforce NOT NULL
    op.alter_column('interviewresult', 'total_score', existing_type=sa.DOUBLE_PRECISION(precision=53), nullable=False)
    
    # interviewsession: enforce NOT NULL + type change
    op.alter_column('interviewsession', 'max_questions', existing_type=sa.INTEGER(), nullable=False)
    op.alter_column('interviewsession', 'status',
               existing_type=postgresql.ENUM('SCHEDULED', 'LIVE', 'COMPLETED', 'EXPIRED', 'CANCELLED', name='interviewstatus'),
               server_default=None, existing_nullable=False)
    op.alter_column('interviewsession', 'current_status',
               existing_type=postgresql.ENUM('INVITED', 'LINK_ACCESSED', 'AUTHENTICATED', 'ENROLLMENT_STARTED', 'ENROLLMENT_COMPLETED', 'INTERVIEW_ACTIVE', 'INTERVIEW_PAUSED', 'INTERVIEW_COMPLETED', 'SUSPENDED', name='candidatestatus'),
               type_=sqlmodel.sql.sqltypes.AutoString(), nullable=False)
    op.alter_column('interviewsession', 'last_activity', existing_type=postgresql.TIMESTAMP(), nullable=False)
    op.alter_column('interviewsession', 'warning_count', existing_type=sa.INTEGER(), server_default=None, existing_nullable=False)
    op.alter_column('interviewsession', 'max_warnings', existing_type=sa.INTEGER(), server_default=None, existing_nullable=False)
    op.alter_column('interviewsession', 'is_suspended', existing_type=sa.BOOLEAN(), server_default=None, existing_nullable=False)
    
    # proctoringevent: enforce NOT NULL
    op.alter_column('proctoringevent', 'details', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('proctoringevent', 'severity', existing_type=sa.VARCHAR(), server_default=None, existing_nullable=False)
    op.alter_column('proctoringevent', 'triggered_warning', existing_type=sa.BOOLEAN(), server_default=None, existing_nullable=False)
    
    # questionpaper: rename admin_id -> adminUser, add question_count/total_marks
    op.add_column('questionpaper', sa.Column('adminUser', sa.Integer(), nullable=True))
    op.add_column('questionpaper', sa.Column('question_count', sa.Integer(), nullable=False, server_default=sa.text('0')))
    op.add_column('questionpaper', sa.Column('total_marks', sa.Integer(), nullable=False, server_default=sa.text('0')))
    op.alter_column('questionpaper', 'description', existing_type=sa.VARCHAR(), nullable=False)
    op.create_foreign_key(None, 'questionpaper', 'user', ['adminUser'], ['id'])
    op.drop_column('questionpaper', 'admin_id')
    
    # questions: enforce NOT NULL
    op.alter_column('questions', 'content', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('questions', 'question_text', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('questions', 'topic', existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column('questions', 'response_type', existing_type=sa.VARCHAR(), server_default=None, existing_nullable=False)
    
    # statustimeline: enforce NOT NULL
    op.alter_column('statustimeline', 'context_data', existing_type=sa.VARCHAR(), nullable=False)
    
    # user: add access_token
    op.add_column('user', sa.Column('access_token', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    
    # --- Part 2: Remove candidate_name/admin_name (from 7437a699d68c) ---
    op.drop_column('interviewsession', 'candidate_name')
    op.drop_column('interviewsession', 'admin_name')


def downgrade() -> None:
    """Downgrade schema."""
    # --- Reverse Part 2 ---
    op.add_column('interviewsession', sa.Column('admin_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('interviewsession', sa.Column('candidate_name', sa.VARCHAR(), autoincrement=False, nullable=True))
    
    # --- Reverse Part 1 ---
    op.drop_column('user', 'access_token')
    op.alter_column('statustimeline', 'context_data', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('questions', 'response_type', existing_type=sa.VARCHAR(), server_default=sa.text("'audio'::character varying"), existing_nullable=False)
    op.alter_column('questions', 'topic', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('questions', 'question_text', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('questions', 'content', existing_type=sa.VARCHAR(), nullable=True)
    op.add_column('questionpaper', sa.Column('admin_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'questionpaper', type_='foreignkey')
    op.create_foreign_key(op.f('questionbank_admin_id_fkey'), 'questionpaper', 'user', ['admin_id'], ['id'])
    op.alter_column('questionpaper', 'description', existing_type=sa.VARCHAR(), nullable=True)
    op.drop_column('questionpaper', 'total_marks')
    op.drop_column('questionpaper', 'question_count')
    op.drop_column('questionpaper', 'adminUser')
    op.alter_column('proctoringevent', 'triggered_warning', existing_type=sa.BOOLEAN(), server_default=sa.text('false'), existing_nullable=False)
    op.alter_column('proctoringevent', 'severity', existing_type=sa.VARCHAR(), server_default=sa.text("'info'::character varying"), existing_nullable=False)
    op.alter_column('proctoringevent', 'details', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('interviewsession', 'is_suspended', existing_type=sa.BOOLEAN(), server_default=sa.text('false'), existing_nullable=False)
    op.alter_column('interviewsession', 'max_warnings', existing_type=sa.INTEGER(), server_default=sa.text('3'), existing_nullable=False)
    op.alter_column('interviewsession', 'warning_count', existing_type=sa.INTEGER(), server_default=sa.text('0'), existing_nullable=False)
    op.alter_column('interviewsession', 'last_activity', existing_type=postgresql.TIMESTAMP(), nullable=True)
    op.alter_column('interviewsession', 'current_status',
               existing_type=sqlmodel.sql.sqltypes.AutoString(),
               type_=postgresql.ENUM('INVITED', 'LINK_ACCESSED', 'AUTHENTICATED', 'ENROLLMENT_STARTED', 'ENROLLMENT_COMPLETED', 'INTERVIEW_ACTIVE', 'INTERVIEW_PAUSED', 'INTERVIEW_COMPLETED', 'SUSPENDED', name='candidatestatus'),
               nullable=True)
    op.alter_column('interviewsession', 'status',
               existing_type=postgresql.ENUM('SCHEDULED', 'LIVE', 'COMPLETED', 'EXPIRED', 'CANCELLED', name='interviewstatus'),
               server_default=sa.text("'SCHEDULED'::interviewstatus"), existing_nullable=False)
    op.alter_column('interviewsession', 'max_questions', existing_type=sa.INTEGER(), nullable=True)
    op.alter_column('interviewresult', 'total_score', existing_type=sa.DOUBLE_PRECISION(precision=53), nullable=True)
    op.alter_column('answers', 'transcribed_text', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('answers', 'audio_path', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('answers', 'score', existing_type=sa.DOUBLE_PRECISION(precision=53), nullable=True)
    op.alter_column('answers', 'feedback', existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column('answers', 'candidate_answer', existing_type=sa.VARCHAR(), nullable=True)
