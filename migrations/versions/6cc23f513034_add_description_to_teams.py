"""add description to teams

Revision ID: 6cc23f513034
Revises: add_completed_at_to_habits
Create Date: 2025-04-22 19:05:21.354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6cc23f513034'
down_revision: Union[str, None] = 'add_completed_at_to_habits'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонку description в таблицу teams
    op.add_column('teams', sa.Column('description', sa.String(), nullable=True))


def downgrade() -> None:
    # Удаляем колонку description из таблицы teams
    op.drop_column('teams', 'description')
