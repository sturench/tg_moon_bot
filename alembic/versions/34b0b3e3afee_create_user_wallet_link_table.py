"""create user wallet link table

Revision ID: 34b0b3e3afee
Revises: 766a535f935b
Create Date: 2022-01-26 16:30:07.322591

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '34b0b3e3afee'
down_revision = '766a535f935b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users_wallets',
        sa.Column(
            'user_id', sa.Integer,
            sa.ForeignKey('user.id'), primary_key=True
        ),
        sa.Column(
            'wallet_id', sa.Integer,
            sa.ForeignKey('wallet.id'), primary_key=True
        )
    )


def downgrade():
    op.drop_table('users_wallets')
