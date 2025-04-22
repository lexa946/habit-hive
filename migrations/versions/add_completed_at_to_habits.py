"""add completed_at to habits

Revision ID: add_completed_at_to_habits
Revises: b424326f0834
Create Date: 2024-04-22 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_completed_at_to_habits'
down_revision = 'b424326f0834'
branch_labels = None
depends_on = None


def upgrade():
    # Add completed_at column
    op.add_column('habits', sa.Column('completed_at', sa.Date(), nullable=True))
    
    # Update existing completed habits with current date
    op.execute("""
        UPDATE habits 
        SET completed_at = CURRENT_DATE 
        WHERE is_completed = true
    """)


def downgrade():
    # Remove completed_at column
    op.drop_column('habits', 'completed_at') 