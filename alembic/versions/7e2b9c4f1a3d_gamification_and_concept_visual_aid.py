"""gamification (xp, streaks) and concept visual_aid

Revision ID: 7e2b9c4f1a3d
Revises: c1c1f0e4a9f2
Create Date: 2026-09-03 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e2b9c4f1a3d'
down_revision: Union[str, Sequence[str], None] = 'c1c1f0e4a9f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('concepts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('visual_aid', sa.String(length=32), nullable=True))
        # The next `db.seed` sets this from content/*.yaml; nullable here is
        # the real steady state (most concepts have no chart), not a bridge.

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('xp', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('last_practiced_on', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_practiced_on')
        batch_op.drop_column('longest_streak')
        batch_op.drop_column('current_streak')
        batch_op.drop_column('xp')

    with op.batch_alter_table('concepts', schema=None) as batch_op:
        batch_op.drop_column('visual_aid')
