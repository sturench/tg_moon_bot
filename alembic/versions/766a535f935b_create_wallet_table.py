"""create wallet table

Revision ID: 766a535f935b
Revises: 5477995e87bf
Create Date: 2022-01-26 15:45:47.499124

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '766a535f935b'
down_revision = '5477995e87bf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'wallet',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('wallet_address', sa.VARCHAR(100)),
    )



def downgrade():
    op.drop_table('wallet')

