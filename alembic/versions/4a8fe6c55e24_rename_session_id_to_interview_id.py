"""rename_session_id_to_interview_id

Revision ID: 4a8fe6c55e24
Revises: a961e08d049d
Create Date: 2026-02-11 17:07:35

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8fe6c55e24'
down_revision: Union[str, None] = 'a961e08d049d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename session_id to interview_id in all tables with foreign keys to interviewsession
    op.alter_column('sessionquestion', 'session_id', new_column_name='interview_id')
    op.alter_column('proctoringevent', 'session_id', new_column_name='interview_id')
    op.alter_column('statustimeline', 'session_id', new_column_name='interview_id')
    op.alter_column('interviewresponse', 'session_id', new_column_name='interview_id')


def downgrade() -> None:
    # Revert the column names back to session_id
    op.alter_column('interviewresponse', 'interview_id', new_column_name='session_id')
    op.alter_column('statustimeline', 'interview_id', new_column_name='session_id')
    op.alter_column('proctoringevent', 'interview_id', new_column_name='session_id')
    op.alter_column('sessionquestion', 'interview_id', new_column_name='session_id')
