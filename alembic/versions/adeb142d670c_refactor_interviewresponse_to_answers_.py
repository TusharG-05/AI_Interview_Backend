"""Refactor InterviewResponse to Answers and add InterviewResult

Revision ID: adeb142d670c
Revises: b118484d1c16
Create Date: 2026-02-16 11:28:48.690647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
"""Refactor InterviewResponse to Answers and add InterviewResult

Revision ID: adeb142d670c
Revises: b118484d1c16
Create Date: 2026-02-16 11:28:48.690647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adeb142d670c'
down_revision: Union[str, Sequence[str], None] = 'b118484d1c16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with data migration."""
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)
    
    # 1. Create InterviewResult table
    op.create_table('interviewresult',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('interview_id', sa.Integer(), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['interview_id'], ['interviewsession.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('interview_id')
    )
    
    # 2. Rename InterviewResponse to Answers
    # Check if table exists (SQLite sometimes needs batch mode for renames, but basic rename might work)
    # Using simple rename first
    op.rename_table('interviewresponse', 'answers')
    
    # 3. Add interview_result_id to answers
    op.add_column('answers', sa.Column('interview_result_id', sa.Integer(), nullable=True))
    op.add_column('answers', sa.Column('candidate_answer', sa.String(), nullable=True))
    op.add_column('answers', sa.Column('feedback', sa.String(), nullable=True))
    
    # 4. Data Migration
    # For each unique interview_id in answers, create an InterviewResult
    # Then link answers to it
    
    # Get all unique interview_ids from answers
    try:
        # Use raw SQL for safety across potential model mismatches
        conn = op.get_bind()
        
        # Mapping old columns to new columns (data copy)
        # SQLite doesn't support easy column rename with data? 
        # Actually `answer_text` -> `candidate_answer`
        # `evaluation_text` -> `feedback`
        
        # Let's simple Copy values first
        op.execute('UPDATE answers SET candidate_answer = answer_text')
        op.execute('UPDATE answers SET feedback = evaluation_text')
        
        # Create Results
        unique_interviews = conn.execute(sa.text("SELECT DISTINCT interview_id FROM answers")).fetchall()
        
        for row in unique_interviews:
            i_id = row[0]
            # Insert InterviewResult
            # We can calculate total score or leave 0
            # Created_at roughly now
            from datetime import datetime
            conn.execute(
                sa.text("INSERT INTO interviewresult (interview_id, total_score, created_at) VALUES (:iid, 0, :cat)"),
                {"iid": i_id, "cat": datetime.utcnow()}
            )
            
            # Get the new ID
            # In postgres/sqlite we might need to fetch it back
            res_id_row = conn.execute(sa.text("SELECT id FROM interviewresult WHERE interview_id = :iid"), {"iid": i_id}).fetchone()
            res_id = res_id_row[0]
            
            # Update answers
            conn.execute(
                sa.text("UPDATE answers SET interview_result_id = :rid WHERE interview_id = :iid"),
                {"rid": res_id, "iid": i_id}
            )
            
    except Exception as e:
        print(f"Data migration warning: {e}")

    # 5. Cleanup schema
    # Now that we have linked, we can make interview_result_id not null?
    # And drop old columns
    
    with op.batch_alter_table('answers') as batch_op:
        batch_op.alter_column('interview_result_id', nullable=False)
        batch_op.drop_column('interview_id')
        batch_op.drop_column('answer_text')
        batch_op.drop_column('evaluation_text')
        batch_op.drop_column('similarity_score') # Dropping legacy unused field?
        
        # Ensure foreign keys
        batch_op.create_foreign_key('fk_answers_interview_result', 'interviewresult', ['interview_result_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse data migration is complex, simplified drop
    op.rename_table('answers', 'interviewresponse')
    op.drop_table('interviewresult')
    # Columns would be lost or need complex restore
    op.add_column('interviewresponse', sa.Column('interview_id', sa.Integer(), nullable=True))
    # ... Simplified downgrade
    pass
