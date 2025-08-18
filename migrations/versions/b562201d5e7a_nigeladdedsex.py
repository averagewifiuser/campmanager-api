from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b562201d5e7a'
down_revision = '429a09c34ba2'
branch_labels = None
depends_on = None

# define the enum separately so we can use it for both upgrade/downgrade
sex_enum = sa.Enum('male', 'female', 'other', name='sex')


def upgrade():
    # Create enum type first
    sex_enum.create(op.get_bind(), checkfirst=True)

    with op.batch_alter_table('registrations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sex', sex_enum, nullable=False, server_default='other'))


def downgrade():
    with op.batch_alter_table('registrations', schema=None) as batch_op:
        batch_op.drop_column('sex')

    # Drop enum type
    sex_enum.drop(op.get_bind(), checkfirst=True)
