"""financial update

Revision ID: 0f5c3c84dbd8
Revises: 3e0d9111b21d
Create Date: 2025-09-22 18:06:32.409100

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f5c3c84dbd8'
down_revision = '3e0d9111b21d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('financial_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recorded_by', sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_financial_transactions_recorded_by_users",  # constraint name
            "users",                # referred table
            ["recorded_by"],        # local columns
            ["id"]                  # remote columns
        )


def downgrade():
    with op.batch_alter_table('financial_transactions', schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_financial_transactions_recorded_by_users",
            type_="foreignkey"
        )
        batch_op.drop_column("recorded_by")
