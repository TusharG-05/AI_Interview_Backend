"""add_cascade_delete_v2

Revision ID: 41958c02d377
Revises: 52e48ec09cdf
Create Date: 2026-02-24 11:28:34.956716

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '41958c02d377'
down_revision: Union[str, Sequence[str], None] = '52e48ec09cdf'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Update 'answers' table
    # We use a safer way to drop and create constraints
    op.drop_constraint('answers_interview_result_id_fkey', 'answers', type_='foreignkey')
    op.create_foreign_key('answers_interview_result_id_fkey', 'answers', 'interviewresult', ['interview_result_id'], ['id'], ondelete='CASCADE')

    # 2. Update 'interviewresult' table
    op.drop_constraint('interviewresult_interview_id_fkey', 'interviewresult', type_='foreignkey')
    op.create_foreign_key('interviewresult_interview_id_fkey', 'interviewresult', 'interviewsession', ['interview_id'], ['id'], ondelete='CASCADE')

    # 3. Update 'proctoringevent' table
    op.drop_constraint('proctoringevent_interview_id_fkey', 'proctoringevent', type_='foreignkey')
    op.create_foreign_key('proctoringevent_interview_id_fkey', 'proctoringevent', 'interviewsession', ['interview_id'], ['id'], ondelete='CASCADE')

    # 4. Update 'sessionquestion' table
    op.drop_constraint('sessionquestion_interview_id_fkey', 'sessionquestion', type_='foreignkey')
    op.create_foreign_key('sessionquestion_interview_id_fkey', 'sessionquestion', 'interviewsession', ['interview_id'], ['id'], ondelete='CASCADE')

    # 5. Update 'statustimeline' table
    op.drop_constraint('statustimeline_interview_id_fkey', 'statustimeline', type_='foreignkey')
    op.create_foreign_key('statustimeline_interview_id_fkey', 'statustimeline', 'interviewsession', ['interview_id'], ['id'], ondelete='CASCADE')

def downgrade() -> None:
    op.drop_constraint('statustimeline_interview_id_fkey', 'statustimeline', type_='foreignkey')
    op.create_foreign_key('statustimeline_interview_id_fkey', 'statustimeline', 'interviewsession', ['interview_id'], ['id'])
    
    op.drop_constraint('sessionquestion_interview_id_fkey', 'sessionquestion', type_='foreignkey')
    op.create_foreign_key('sessionquestion_interview_id_fkey', 'sessionquestion', 'interviewsession', ['interview_id'], ['id'])
    
    op.drop_constraint('proctoringevent_interview_id_fkey', 'proctoringevent', type_='foreignkey')
    op.create_foreign_key('proctoringevent_interview_id_fkey', 'proctoringevent', 'interviewsession', ['interview_id'], ['id'])
    
    op.drop_constraint('interviewresult_interview_id_fkey', 'interviewresult', type_='foreignkey')
    op.create_foreign_key('interviewresult_interview_id_fkey', 'interviewresult', 'interviewsession', ['interview_id'], ['id'])
    
    op.drop_constraint('answers_interview_result_id_fkey', 'answers', type_='foreignkey')
    op.create_foreign_key('answers_interview_result_id_fkey', 'answers', 'interviewresult', ['interview_result_id'], ['id'])
