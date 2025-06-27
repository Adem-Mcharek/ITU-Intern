"""Add meeting notes path column to meeting table

Revision ID: 20250103_add_meeting_notes
Revises: 20250103_add_itu_summary
Create Date: 2025-01-03 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250103_add_meeting_notes'
down_revision = '20250103_add_itu_summary'
branch_labels = None
depends_on = None

def upgrade():
    """Add notes_path column to meeting table"""
    # Add the new column
    op.add_column('meeting', sa.Column('notes_path', sa.String(512), nullable=True))

def downgrade():
    """Remove notes_path column from meeting table"""
    # Remove the column
    op.drop_column('meeting', 'notes_path') 