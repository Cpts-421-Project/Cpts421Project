"""add_review_status_to_objects

Revision ID: e1a2b3c4d5e6
Revises: d86f7k1a32b9
Create Date: 2026-10-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5e6'
down_revision: Union[str, None] = 'd86f7k1a32b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(conn)

    # Check if table objects exists
    if 'objects' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('objects')]
        if 'review_status' not in columns:
            op.add_column(
                'objects',
                sa.Column('review_status', sa.String(length=50), server_default='accepted', nullable=True)
            )
            # Mark any existing records as accepted
            conn.execute(sa.text("UPDATE objects SET review_status = 'accepted' WHERE review_status IS NULL"))

        indices = [idx['name'] for idx in inspector.get_indexes('objects')]
        if 'ix_objects_review_status' not in indices:
            op.create_index('ix_objects_review_status', 'objects', ['review_status'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(conn)

    if 'objects' in inspector.get_table_names():
        indices = [idx['name'] for idx in inspector.get_indexes('objects')]
        if 'ix_objects_review_status' in indices:
            op.drop_index('ix_objects_review_status', table_name='objects')

        columns = [c['name'] for c in inspector.get_columns('objects')]
        if 'review_status' in columns:
            op.drop_column('objects', 'review_status')
