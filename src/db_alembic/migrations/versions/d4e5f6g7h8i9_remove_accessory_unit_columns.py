"""Remove accessory unit columns

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-19 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop unit columns from accessories tables."""
    with op.batch_alter_table("accessories", schema=None) as batch_op:
        batch_op.drop_constraint("ck_accessory_unit", type_="check")
        batch_op.drop_column("unit")

    with op.batch_alter_table(
        "project_cabinet_accessory_snapshots", schema=None
    ) as batch_op:
        batch_op.drop_constraint("ck_project_accessory_unit", type_="check")
        batch_op.drop_column("unit")


def downgrade() -> None:
    """Re-add unit columns to accessories tables."""
    with op.batch_alter_table("accessories", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("unit", sa.String(10), nullable=False, server_default="szt")
        )
        batch_op.create_check_constraint("ck_accessory_unit", "unit IN ('szt', 'kpl')")

    with op.batch_alter_table(
        "project_cabinet_accessory_snapshots", schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column("unit", sa.String(10), nullable=False, server_default="szt")
        )
        batch_op.create_check_constraint(
            "ck_project_accessory_unit", "unit IN ('szt', 'kpl')"
        )
