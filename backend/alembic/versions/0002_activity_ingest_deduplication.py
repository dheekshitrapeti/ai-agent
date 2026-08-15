"""add activity ingestion deduplication"""

from alembic import op


revision = "0002_activity_dedup"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_activities_user_source_external_id",
        "activities",
        ["user_id", "source", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_activities_user_source_external_id", "activities", type_="unique")
