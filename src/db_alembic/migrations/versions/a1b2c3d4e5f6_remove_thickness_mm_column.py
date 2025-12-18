"""Remove thickness_mm column from cabinet_parts and project_cabinet_parts

Revision ID: a1b2c3d4e5f6
Revises: 8fcefcd73ebc
Create Date: 2025-01-01 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8fcefcd73ebc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove thickness_mm column from parts tables."""
    # Remove thickness_mm from cabinet_parts
    with op.batch_alter_table("cabinet_parts", schema=None) as batch_op:
        batch_op.drop_column("thickness_mm")

    # Remove thickness_mm from project_cabinet_parts
    with op.batch_alter_table("project_cabinet_parts", schema=None) as batch_op:
        batch_op.drop_column("thickness_mm")


def downgrade() -> None:
    """Re-add thickness_mm column to parts tables."""
    # Add thickness_mm back to cabinet_parts
    with op.batch_alter_table("cabinet_parts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("thickness_mm", sa.Integer(), nullable=True))

    # Add thickness_mm back to project_cabinet_parts
    with op.batch_alter_table("project_cabinet_parts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("thickness_mm", sa.Integer(), nullable=True))
