"""create users table

Revision ID: 5477995e87bf
Revises: 
Create Date: 2022-01-26 15:41:20.414056

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5477995e87bf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('telegram_id', sa.BigInteger)
    )


def downgrade():
    op.drop_table('user')
