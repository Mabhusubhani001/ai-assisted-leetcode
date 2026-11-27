"""add driver_code to questions

Revision ID: b78e1245a90c
Revises: ea64eee815ba
Create Date: 2026-11-28 01:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b78e1245a90c'
down_revision: Union[str, Sequence[str], None] = 'ea64eee815ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add driver_code JSONB column for multi-language test harnesses."""
    op.add_column(
        'questions',
        sa.Column(
            'driver_code',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False
        )
    )


def downgrade() -> None:
    """Revert driver_code column addition."""
    op.drop_column('questions', 'driver_code')
