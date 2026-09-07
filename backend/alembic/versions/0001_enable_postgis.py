"""enable postgis extension

Revision ID: 0001_enable_postgis
Revises:
Create Date: 2026-09-07
"""

from alembic import op

revision = "0001_enable_postgis"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS postgis")
