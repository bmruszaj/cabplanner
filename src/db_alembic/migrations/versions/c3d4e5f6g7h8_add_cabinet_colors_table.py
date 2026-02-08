"""Add cabinet_colors table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-08 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cabinet_colors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("normalized_name", sa.String(length=120), nullable=False),
        sa.Column("hex_code", sa.String(length=7), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column(
            "usage_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source IN ('system', 'user')", name="ck_cabinet_color_source"
        ),
        sa.CheckConstraint("usage_count >= 0", name="ck_cabinet_color_usage_nonneg"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name"),
    )

    with op.batch_alter_table("cabinet_colors", schema=None) as batch_op:
        batch_op.create_index(
            "ix_cabinet_colors_last_used_at", ["last_used_at"], unique=False
        )
        batch_op.create_index("ix_cabinet_colors_source", ["source"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("cabinet_colors", schema=None) as batch_op:
        batch_op.drop_index("ix_cabinet_colors_source")
        batch_op.drop_index("ix_cabinet_colors_last_used_at")

    op.drop_table("cabinet_colors")
