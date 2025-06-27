"""Add ITU summary column to meeting table

Revision ID: 20250103_add_itu_summary
Revises: 20241226_add_developer_role
Create Date: 2025-01-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250103_add_itu_summary'
down_revision = '20241226_add_developer_role'
branch_labels = None
depends_on = None

def upgrade():
    """Add itu_summary column to meeting table"""
    # Add the new column
    op.add_column('meeting', sa.Column('itu_summary', sa.Text(), nullable=True))

def downgrade():
    """Remove itu_summary column from meeting table"""
    # Remove the column
    op.drop_column('meeting', 'itu_summary') 