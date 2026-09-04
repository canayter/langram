"""concept recurs_in

Revision ID: 9a4d3e1c7f2b
Revises: 7e2b9c4f1a3d
Create Date: 2026-09-04 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = '9a4d3e1c7f2b'
down_revision: Union[str, Sequence[str], None] = '7e2b9c4f1a3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('concepts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recurs_in', sa.JSON(), nullable=False, server_default='[]'))
        # The next `db.seed` overwrites every concept's recurs_in from
        # content/*.yaml; the default is only a bridge for existing rows.


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('concepts', schema=None) as batch_op:
        batch_op.drop_column('recurs_in')
