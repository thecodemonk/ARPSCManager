"""make member email nullable

Revision ID: a3f9b2c4d701
Revises: e730cd1d99a4
Create Date: 2026-05-03 00:00:00.000000

Allows admins to track members who don't have an email address (paper-record
holdovers, members who declined to share one). Email is still unique when
present; SQLite permits multiple NULLs in a UNIQUE column. Members without
email simply can't use the magic-link login.
"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f9b2c4d701'
down_revision = 'e730cd1d99a4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('members') as batch:
        batch.alter_column('email', existing_type=sa.Text(), nullable=True)


def downgrade():
    # Backfill empty/null emails with a placeholder before re-imposing NOT NULL
    # so the downgrade doesn't fail on rows that were created without one.
    op.execute("UPDATE members SET email = 'noemail-' || id || '@local' WHERE email IS NULL OR email = ''")
    with op.batch_alter_table('members') as batch:
        batch.alter_column('email', existing_type=sa.Text(), nullable=False)
