"""Replace sku with unit in accessories tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-20 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace sku with unit in accessories and project_cabinet_accessory_snapshots."""
    # Accessories table: drop sku, add unit
    with op.batch_alter_table("accessories", schema=None) as batch_op:
        batch_op.drop_constraint("uq_accessory_sku", type_="unique")
        batch_op.drop_index("ix_accessories_sku")
        batch_op.drop_column("sku")
        batch_op.add_column(
            sa.Column("unit", sa.String(10), nullable=False, server_default="szt")
        )
        batch_op.create_check_constraint("ck_accessory_unit", "unit IN ('szt', 'kpl')")

    # Project cabinet accessory snapshots table: replace sku with unit
    with op.batch_alter_table(
        "project_cabinet_accessory_snapshots", schema=None
    ) as batch_op:
        batch_op.drop_column("sku")
        batch_op.add_column(
            sa.Column("unit", sa.String(10), nullable=False, server_default="szt")
        )
        batch_op.create_check_constraint(
            "ck_project_accessory_unit", "unit IN ('szt', 'kpl')"
        )


def downgrade() -> None:
    """Restore sku column, remove unit from accessories tables."""
    # Accessories table: drop unit, add sku back
    with op.batch_alter_table("accessories", schema=None) as batch_op:
        batch_op.drop_constraint("ck_accessory_unit", type_="check")
        batch_op.drop_column("unit")
        batch_op.add_column(
            sa.Column("sku", sa.String(120), nullable=False, server_default="")
        )
        batch_op.create_unique_constraint("uq_accessory_sku", ["sku"])
        batch_op.create_index("ix_accessories_sku", ["sku"])

    # Project cabinet accessory snapshots table: restore sku
    with op.batch_alter_table(
        "project_cabinet_accessory_snapshots", schema=None
    ) as batch_op:
        batch_op.drop_constraint("ck_project_accessory_unit", type_="check")
        batch_op.drop_column("unit")
        batch_op.add_column(
            sa.Column("sku", sa.String(120), nullable=False, server_default="")
        )
