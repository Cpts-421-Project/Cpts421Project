"""add_rejected_artifacts_table

Revision ID: c3d4e5f6a7b0
Revises: b2c3d4e5f6a9
Create Date: 2026-11-22 15:25:00.000000

"""
import re
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b0'
down_revision: Union[str, None] = 'b2c3d4e5f6a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MET_URL_RE = re.compile(r"metmuseum\.org/art/collection/search/(\d+)", re.IGNORECASE)
_MET_SRC_RE = re.compile(r"Met Object ID\s+(\d+)", re.IGNORECASE)
_VAM_URL_RE = re.compile(r"collections\.vam\.ac\.uk/item/([A-Za-z0-9_-]+)", re.IGNORECASE)
_VAM_SRC_RE = re.compile(r"V&A\s+([A-Za-z0-9_-]+)", re.IGNORECASE)
_AIC_URL_RE = re.compile(r"artic\.edu/artworks/(\d+)", re.IGNORECASE)
_CMA_URL_RE = re.compile(r"clevelandart\.org/art/([^/?#]+)", re.IGNORECASE)
_CMA_INV_RE = re.compile(r"^CMA-(\d+)$", re.IGNORECASE)
_BM_URL_RE = re.compile(r"britishmuseum\.org/collection/object/([^/?#]+)", re.IGNORECASE)
_BM_WD_URL_RE = re.compile(r"wikidata\.org/wiki/(Q\d+)", re.IGNORECASE)
_BM_SRC_RE = re.compile(r"\bBM\s+(Q\d+)\b", re.IGNORECASE)


def _norm_key(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip().lower()
    return cleaned or None


def _norm_url(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip().rstrip("/").lower()
    return cleaned or None


def _extract_provenance(
    external_url: Optional[str],
    source_identifiers: List[str],
    present_location: Optional[str],
    inventory_number: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    url = (external_url or "").strip()
    inv = (inventory_number or "").strip()
    loc = (present_location or "").lower()

    for src_id in source_identifiers:
        m = _MET_SRC_RE.search(src_id)
        if m:
            return "met", m.group(1)
        m = _VAM_SRC_RE.search(src_id)
        if m:
            return "vam", m.group(1)
        m = _BM_SRC_RE.search(src_id)
        if m:
            return "bm", m.group(1).upper()

    if url:
        m = _MET_URL_RE.search(url)
        if m:
            return "met", m.group(1)
        m = _VAM_URL_RE.search(url)
        if m:
            return "vam", m.group(1)
        m = _AIC_URL_RE.search(url)
        if m:
            return "aic", m.group(1)
        m = _CMA_URL_RE.search(url)
        if m:
            cma_token = m.group(1)
            cma_match = _CMA_INV_RE.match(cma_token)
            if cma_match:
                return "cma", cma_match.group(1)
            inv_match = _CMA_INV_RE.match(inv)
            return "cma", (inv_match.group(1) if inv_match else None)
        m = _BM_WD_URL_RE.search(url)
        if m:
            return "bm", m.group(1).upper()
        m = _BM_URL_RE.search(url)
        if m:
            return "bm", m.group(1)

    inv_match = _CMA_INV_RE.match(inv)
    if inv_match:
        return "cma", inv_match.group(1)

    if "metropolitan museum" in loc:
        return "met", None
    if "cleveland museum" in loc:
        return "cma", None
    if "art institute of chicago" in loc:
        return "aic", None
    if "victoria and albert" in loc:
        return "vam", None
    if "british museum" in loc:
        return "bm", None

    return None, None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'rejected_artifacts' not in table_names:
        op.create_table(
            'rejected_artifacts',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('museum_id', sa.String(length=32), nullable=True),
            sa.Column('source_record_id', sa.String(length=100), nullable=True),
            sa.Column('inventory_number', sa.String(length=100), nullable=True),
            sa.Column('external_url', sa.String(length=500), nullable=True),
            sa.Column('object_type', sa.String(length=255), nullable=True),
            sa.Column('present_location', sa.String(length=255), nullable=True),
            sa.Column('date_display', sa.String(length=255), nullable=True),
            sa.Column(
                'rejected_at',
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index('ix_rejected_artifacts_museum_id', 'rejected_artifacts', ['museum_id'], unique=False)
        op.create_index('ix_rejected_artifacts_source_record_id', 'rejected_artifacts', ['source_record_id'], unique=False)
        op.create_index('ix_rejected_artifacts_inventory_number', 'rejected_artifacts', ['inventory_number'], unique=False)
        op.create_index('ix_rejected_artifacts_external_url', 'rejected_artifacts', ['external_url'], unique=False)

    if 'objects' in table_names:
        rejected_table = sa.table(
            'rejected_artifacts',
            sa.column('museum_id', sa.String(length=32)),
            sa.column('source_record_id', sa.String(length=100)),
            sa.column('inventory_number', sa.String(length=100)),
            sa.column('external_url', sa.String(length=500)),
            sa.column('object_type', sa.String(length=255)),
            sa.column('present_location', sa.String(length=255)),
            sa.column('date_display', sa.String(length=255)),
        )
        existing_rows = conn.execute(
            sa.select(
                rejected_table.c.museum_id,
                rejected_table.c.source_record_id,
                rejected_table.c.inventory_number,
                rejected_table.c.external_url,
                rejected_table.c.object_type,
                rejected_table.c.present_location,
                rejected_table.c.date_display,
            )
        ).fetchall()

        seen_museum_keys: Set[Tuple[str, str]] = set()
        seen_invs: Set[str] = set()
        seen_urls: Set[str] = set()
        seen_sigs: Set[Tuple[str, str, str]] = set()

        for mid, sid, inv, ext_url, otype, ploc, ddisp in existing_rows:
            if mid and sid:
                seen_museum_keys.add((mid.lower(), sid.lower()))
            n_inv = _norm_key(inv)
            if n_inv:
                seen_invs.add(n_inv)
            n_url = _norm_url(ext_url)
            if n_url:
                seen_urls.add(n_url)
            if otype:
                seen_sigs.add((otype.strip().lower(), (ploc or "").strip().lower(), (ddisp or "").strip().lower()))

        src_ids_by_obj: Dict[int, List[str]] = {}
        if 'images' in table_names:
            images_table = sa.table(
                'images',
                sa.column('object_id', sa.Integer()),
                sa.column('source_identifier', sa.String(length=255)),
            )
            img_rows = conn.execute(
                sa.select(images_table.c.object_id, images_table.c.source_identifier).where(
                    images_table.c.source_identifier.is_not(None)
                )
            ).fetchall()
            for obj_id, src_id in img_rows:
                if obj_id is not None and src_id and str(src_id).strip():
                    src_ids_by_obj.setdefault(obj_id, []).append(str(src_id).strip())

        objects_table = sa.table(
            'objects',
            sa.column('id', sa.Integer()),
            sa.column('inventory_number', sa.String(length=100)),
            sa.column('external_url', sa.String(length=500)),
            sa.column('object_type', sa.String(length=255)),
            sa.column('present_location', sa.String(length=255)),
            sa.column('date_display', sa.String(length=255)),
            sa.column('review_status', sa.String(length=50)),
        )
        obj_rows = conn.execute(
            sa.select(
                objects_table.c.id,
                objects_table.c.inventory_number,
                objects_table.c.external_url,
                objects_table.c.object_type,
                objects_table.c.present_location,
                objects_table.c.date_display,
            ).where(objects_table.c.review_status == 'rejected')
        ).fetchall()

        to_insert = []
        for obj_id, inv, ext_url, otype, ploc, ddisp in obj_rows:
            mid, sid = _extract_provenance(
                ext_url,
                src_ids_by_obj.get(obj_id, []),
                ploc,
                inv,
            )
            clean_url = ext_url.strip().rstrip("/")[:500] if isinstance(ext_url, str) and ext_url.strip() else None
            clean_inv = inv.strip()[:100] if isinstance(inv, str) and inv.strip() else None
            clean_mid = mid.lower()[:32] if mid else None
            clean_sid = sid.strip()[:100] if sid and sid.strip() else None
            clean_type = otype.strip()[:255] if isinstance(otype, str) and otype.strip() else None
            clean_loc = ploc.strip()[:255] if isinstance(ploc, str) and ploc.strip() else None
            clean_date = ddisp.strip()[:255] if isinstance(ddisp, str) and ddisp.strip() else None

            n_inv = _norm_key(clean_inv)
            n_url = _norm_url(clean_url)
            sig = (
                (clean_type or "").lower(),
                (clean_loc or "").lower(),
                (clean_date or "").lower(),
            ) if clean_type else None

            is_dup = (
                (clean_mid and clean_sid and (clean_mid, clean_sid.lower()) in seen_museum_keys)
                or (n_inv and n_inv in seen_invs)
                or (n_url and n_url in seen_urls)
                or (not n_inv and not n_url and not (clean_mid and clean_sid) and sig and sig in seen_sigs)
            )
            if is_dup:
                continue

            if clean_mid and clean_sid:
                seen_museum_keys.add((clean_mid, clean_sid.lower()))
            if n_inv:
                seen_invs.add(n_inv)
            if n_url:
                seen_urls.add(n_url)
            if sig:
                seen_sigs.add(sig)

            to_insert.append({
                'museum_id': clean_mid,
                'source_record_id': clean_sid,
                'inventory_number': clean_inv,
                'external_url': clean_url,
                'object_type': clean_type,
                'present_location': clean_loc,
                'date_display': clean_date,
            })

        if to_insert:
            op.bulk_insert(rejected_table, to_insert)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    table_names = inspector.get_table_names()

    if 'rejected_artifacts' in table_names:
        existing_indices = {idx['name'] for idx in inspector.get_indexes('rejected_artifacts')}
        for idx_name in (
            'ix_rejected_artifacts_external_url',
            'ix_rejected_artifacts_inventory_number',
            'ix_rejected_artifacts_source_record_id',
            'ix_rejected_artifacts_museum_id',
        ):
            if idx_name in existing_indices:
                op.drop_index(idx_name, table_name='rejected_artifacts')
        op.drop_table('rejected_artifacts')
