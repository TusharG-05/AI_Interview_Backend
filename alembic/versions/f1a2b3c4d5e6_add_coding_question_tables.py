"""add_coding_question_tables

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-03-11

Description:
    1. Creates the `codingquestionpaper` table – mirrors `questionpaper` but
       dedicated to LeetCode-style coding problems.
    2. Creates the `codingquestions` table – stores individual coding problems
       with structured fields (title, problem_statement, examples, constraints,
       starter_code, topic, difficulty, marks).
    3. Adds a nullable `coding_paper_id` FK column to `interviewsession` so an
       interview can be linked to a coding question paper.
    4. Makes `interviewsession.paper_id` nullable (was NOT NULL) so interviews
       can be scheduled with only coding questions and no standard paper.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '47f7bcf4f97d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create codingquestionpaper
    # ------------------------------------------------------------------
    op.create_table(
        'codingquestionpaper',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False, server_default=''),
        sa.Column('adminUser', sa.Integer(), nullable=True),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_marks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['adminUser'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_codingquestionpaper_name'), 'codingquestionpaper', ['name'], unique=False)

    # ------------------------------------------------------------------
    # 2. Create codingquestions
    # ------------------------------------------------------------------
    op.create_table(
        'codingquestions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False, server_default=''),
        sa.Column('problem_statement', sa.String(), nullable=False, server_default=''),
        sa.Column('examples', sa.String(), nullable=False, server_default='[]'),
        sa.Column('constraints', sa.String(), nullable=False, server_default='[]'),
        sa.Column('starter_code', sa.String(), nullable=False, server_default=''),
        sa.Column('topic', sa.String(), nullable=False, server_default='Algorithms'),
        sa.Column('difficulty', sa.String(), nullable=False, server_default='Medium'),
        sa.Column('marks', sa.Integer(), nullable=False, server_default='6'),
        sa.ForeignKeyConstraint(['paper_id'], ['codingquestionpaper.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ------------------------------------------------------------------
    # 3. Add coding_paper_id to interviewsession
    # ------------------------------------------------------------------
    op.add_column(
        'interviewsession',
        sa.Column('coding_paper_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_interviewsession_coding_paper_id',
        'interviewsession', 'codingquestionpaper',
        ['coding_paper_id'], ['id'],
        ondelete='SET NULL'
    )

    # ------------------------------------------------------------------
    # 4. Make interviewsession.paper_id nullable (was NOT NULL)
    # ------------------------------------------------------------------
    with op.batch_alter_table('interviewsession') as batch_op:
        batch_op.alter_column('paper_id', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Reverse step 4
    with op.batch_alter_table('interviewsession') as batch_op:
        batch_op.alter_column('paper_id', existing_type=sa.Integer(), nullable=False)

    # Reverse step 3
    op.drop_constraint('fk_interviewsession_coding_paper_id', 'interviewsession', type_='foreignkey')
    op.drop_column('interviewsession', 'coding_paper_id')

    # Reverse step 2
    op.drop_table('codingquestions')

    # Reverse step 1
    op.drop_index(op.f('ix_codingquestionpaper_name'), table_name='codingquestionpaper')
    op.drop_table('codingquestionpaper')
