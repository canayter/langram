"""concept order within unit

Revision ID: c1c1f0e4a9f2
Revises: a309ab850d6b
Create Date: 2026-09-03 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1c1f0e4a9f2'
down_revision: Union[str, Sequence[str], None] = 'a309ab850d6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('concepts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'))
        # The default is only a bridge for existing rows: the next `db.seed`
        # overwrites every concept's order_index with its real position in
        # content/*.yaml's concepts list.


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('concepts', schema=None) as batch_op:
        batch_op.drop_column('order_index')
