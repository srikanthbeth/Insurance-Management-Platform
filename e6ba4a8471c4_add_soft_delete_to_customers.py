"""add soft delete to customers

Revision ID: e6ba4a8471c4
Revises: 3c2debe1a8e3
Create Date: 2026-09-02 10:37:50.776436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6ba4a8471c4'
down_revision: Union[str, Sequence[str], None] = '3c2debe1a8e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_index(
        "ix_customers_is_deleted",
        "customers",
        ["is_deleted"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customers_is_deleted",
        table_name="customers",
    )

    op.drop_column(
        "customers",
        "is_deleted",
    )