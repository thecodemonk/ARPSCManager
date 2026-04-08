"""add member program active flags and audit dates

Revision ID: c1a4e9d2f7b3
Revises: 898fdbab6bea
Create Date: 2026-04-08 00:00:00.000000

Adds three program "interest" + "active" pairs (skywarn, arpsc, siren_testing)
plus per-program activated_at/deactivated_at audit dates and an overall
archived_at. Backfills existing members so current state-report counts and
attendance pickers don't change behavior the moment the migration runs.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1a4e9d2f7b3'
down_revision = '898fdbab6bea'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('members') as batch:
        batch.add_column(sa.Column('interest_siren_testing', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('arpsc_active', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('skywarn_active', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('siren_testing_active', sa.Boolean(), nullable=True))
        batch.add_column(sa.Column('arpsc_activated_at', sa.Date(), nullable=True))
        batch.add_column(sa.Column('arpsc_deactivated_at', sa.Date(), nullable=True))
        batch.add_column(sa.Column('skywarn_activated_at', sa.Date(), nullable=True))
        batch.add_column(sa.Column('skywarn_deactivated_at', sa.Date(), nullable=True))
        batch.add_column(sa.Column('siren_testing_activated_at', sa.Date(), nullable=True))
        batch.add_column(sa.Column('siren_testing_deactivated_at', sa.Date(), nullable=True))
        batch.add_column(sa.Column('archived_at', sa.Date(), nullable=True))

    # Default the new booleans to 0 so SQL filters work correctly.
    op.execute("UPDATE members SET interest_siren_testing = 0 WHERE interest_siren_testing IS NULL")
    op.execute("UPDATE members SET arpsc_active = 0 WHERE arpsc_active IS NULL")
    op.execute("UPDATE members SET skywarn_active = 0 WHERE skywarn_active IS NULL")
    op.execute("UPDATE members SET siren_testing_active = 0 WHERE siren_testing_active IS NULL")

    # Backfill: anyone currently active and ARES/AUXCOMM interested becomes
    # arpsc_active, with their activation dated to when they joined.
    op.execute("""
        UPDATE members
        SET arpsc_active = 1,
            arpsc_activated_at = DATE(created_at)
        WHERE active = 1 AND interest_ares_auxcomm = 1
    """)
    op.execute("""
        UPDATE members
        SET skywarn_active = 1,
            skywarn_activated_at = DATE(created_at)
        WHERE active = 1 AND interest_skywarn = 1
    """)
    # Anyone already archived gets archived_at stamped to today as a best-effort.
    op.execute("UPDATE members SET archived_at = DATE('now') WHERE active = 0 AND archived_at IS NULL")


def downgrade():
    with op.batch_alter_table('members') as batch:
        batch.drop_column('archived_at')
        batch.drop_column('siren_testing_deactivated_at')
        batch.drop_column('siren_testing_activated_at')
        batch.drop_column('skywarn_deactivated_at')
        batch.drop_column('skywarn_activated_at')
        batch.drop_column('arpsc_deactivated_at')
        batch.drop_column('arpsc_activated_at')
        batch.drop_column('siren_testing_active')
        batch.drop_column('skywarn_active')
        batch.drop_column('arpsc_active')
        batch.drop_column('interest_siren_testing')
