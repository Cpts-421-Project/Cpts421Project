"""add_discovery_keywords_table

Revision ID: a1b2c3d4e5f8
Revises: f2b3c4d5e6f7
Create Date: 2026-11-21 21:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f8'
down_revision: Union[str, None] = 'f2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_DISCOVERY_KEYWORDS = (
    'craftsman',
    'glass',
    'potter',
    'workshop',
    'weaver',
    'blacksmith',
    'scribe',
    'sculptor',
)


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'discovery_keywords' not in table_names:
        op.create_table(
            'discovery_keywords',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('keyword', sa.String(length=80), nullable=False, unique=True),
            sa.Column('is_default', sa.Boolean(), server_default=sa.false(), nullable=False),
        )
        op.create_index('ix_discovery_keywords_keyword', 'discovery_keywords', ['keyword'], unique=True)

        keywords_table = sa.table(
            'discovery_keywords',
            sa.column('keyword', sa.String(length=80)),
            sa.column('is_default', sa.Boolean()),
        )
        existing = {
            row[0].lower()
            for row in conn.execute(sa.select(keywords_table.c.keyword)).fetchall()
        }
        to_insert = [
            {'keyword': kw, 'is_default': True}
            for kw in DEFAULT_DISCOVERY_KEYWORDS
            if kw.lower() not in existing
        ]
        if to_insert:
            op.bulk_insert(keywords_table, to_insert)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'discovery_keywords' in table_names:
        existing_indices = {idx['name'] for idx in inspector.get_indexes('discovery_keywords')}
        if 'ix_discovery_keywords_keyword' in existing_indices:
            op.drop_index('ix_discovery_keywords_keyword', table_name='discovery_keywords')
        op.drop_table('discovery_keywords')
