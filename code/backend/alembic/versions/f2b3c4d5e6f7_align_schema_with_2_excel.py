"""align_schema_with_2_excel

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-11-21 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, None] = 'e1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OBJECT_NEW_COLUMNS = [
    ('present_location', sa.String(length=255)),
    ('production_location', sa.String(length=255)),
    ('dimensions_display', sa.String(length=255)),
    ('weight', sa.String(length=100)),
    ('completeness', sa.String(length=255)),
    ('date_basis', sa.Text()),
    ('inscription_present', sa.Boolean()),
    ('inscription_1', sa.Text()),
    ('inscription_2', sa.Text()),
    ('object_group', sa.String(length=255)),
    ('publications', sa.Text()),
    ('caption', sa.Text()),
    ('external_url', sa.String(length=500)),
]

IMAGE_NEW_COLUMNS = [
    ('image_sequence', sa.Integer()),
    ('source_identifier', sa.String(length=255)),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'objects' in table_names:
        existing_obj_cols = {c['name'] for c in inspector.get_columns('objects')}
        for col_name, col_type in OBJECT_NEW_COLUMNS:
            if col_name not in existing_obj_cols:
                op.add_column('objects', sa.Column(col_name, col_type, nullable=True))

        existing_indices = {idx['name'] for idx in inspector.get_indexes('objects')}
        if 'ix_objects_present_location' not in existing_indices:
            op.create_index('ix_objects_present_location', 'objects', ['present_location'], unique=False)

    if 'images' in table_names:
        existing_img_cols = {c['name'] for c in inspector.get_columns('images')}
        for col_name, col_type in IMAGE_NEW_COLUMNS:
            if col_name not in existing_img_cols:
                op.add_column('images', sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'images' in table_names:
        existing_img_cols = {c['name'] for c in inspector.get_columns('images')}
        for col_name, _ in reversed(IMAGE_NEW_COLUMNS):
            if col_name in existing_img_cols:
                op.drop_column('images', col_name)

    if 'objects' in table_names:
        existing_indices = {idx['name'] for idx in inspector.get_indexes('objects')}
        if 'ix_objects_present_location' in existing_indices:
            op.drop_index('ix_objects_present_location', table_name='objects')

        existing_obj_cols = {c['name'] for c in inspector.get_columns('objects')}
        for col_name, _ in reversed(OBJECT_NEW_COLUMNS):
            if col_name in existing_obj_cols:
                op.drop_column('objects', col_name)
