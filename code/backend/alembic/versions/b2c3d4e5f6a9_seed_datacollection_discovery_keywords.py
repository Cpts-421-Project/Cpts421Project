"""seed_datacollection_discovery_keywords

Revision ID: b2c3d4e5f6a9
Revises: a1b2c3d4e5f8
Create Date: 2026-11-21 22:13:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a9'
down_revision: Union[str, None] = 'a1b2c3d4e5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADDITIONAL_DISCOVERY_KEYWORDS = (
    'ancient worker',
    'baker',
    'brewer',
    'farmer',
    'butcher',
    'carpenter',
    'apprentice',
    'glass maker',
    'vitrearii',
    'jeweler',
    'carpenters',
    'craft',
    'ergateri',
    'slave',
    'furnace',
    'kiln',
    'oven',
    'cutter',
    'tailor',
    'carver',
    'smith',
    'mold',
    'glassblower',
    'builder',
    'construction',
    'scene',
    'work',
    'saw',
    'tool',
    'bow',
    'drill',
    'midwife',
    'physician',
    'serf',
    'pesant',
    'hephaestus',
    'sow',
    'driver',
    'carvan',
    'smelt',
    'work scene',
    'Daedalus',
    'Icarus',
    'Vulcan',
    'cobbler',
    'maker',
    'painter',
    'shop',
    'merchant',
    'producer',
    'product',
    'press',
    'grain',
    'Pygmalion',
)


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'discovery_keywords' in table_names:
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
            for kw in ADDITIONAL_DISCOVERY_KEYWORDS
            if kw.lower() not in existing
        ]
        if to_insert:
            op.bulk_insert(keywords_table, to_insert)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'discovery_keywords' in table_names:
        keywords_table = sa.table(
            'discovery_keywords',
            sa.column('keyword', sa.String(length=80)),
            sa.column('is_default', sa.Boolean()),
        )
        op.execute(
            keywords_table.delete().where(
                sa.and_(
                    keywords_table.c.is_default.is_(True),
                    keywords_table.c.keyword.in_(ADDITIONAL_DISCOVERY_KEYWORDS),
                )
            )
        )
