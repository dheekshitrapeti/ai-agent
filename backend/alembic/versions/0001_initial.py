"""initial schema"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    provider = sa.Enum("SLACK", "GMAIL", "GOOGLE_DRIVE", name="integration_provider")
    status = sa.Enum("DISCONNECTED", "CONNECTED", "ERROR", name="integration_status")
    source = sa.Enum("SLACK", "GMAIL", "GOOGLE_DRIVE", name="activity_source")
    activity_type = sa.Enum("MESSAGE", "EMAIL", "DOCUMENT", name="activity_type")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", provider, nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("external_account_id", sa.String(255)),
        sa.Column("access_token_encrypted", sa.Text()),
        sa.Column("refresh_token_encrypted", sa.Text()),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("connected_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_integrations_user_id", "integrations", ["user_id"])
    op.create_index("ix_integrations_provider", "integrations", ["provider"])
    op.create_index("ix_integrations_status", "integrations", ["status"])

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", source, nullable=False),
        sa.Column("activity_type", activity_type, nullable=False),
        sa.Column("external_id", sa.String(512), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("sender", sa.String(500)),
        sa.Column("summary", sa.Text()),
        sa.Column("original_content", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("event_created_at", sa.DateTime(timezone=True)),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for name, table, cols in [
        ("ix_activities_user_id", "activities", ["user_id"]),
        ("ix_activities_source", "activities", ["source"]),
        ("ix_activities_activity_type", "activities", ["activity_type"]),
        ("ix_activities_user_created_at", "activities", ["user_id", "created_at"]),
        ("ix_activities_source_event_created_at", "activities", ["source", "event_created_at"]),
    ]:
        op.create_index(name, table, cols)


def downgrade() -> None:
    for name in [
        "ix_activities_source_event_created_at",
        "ix_activities_user_created_at",
        "ix_activities_activity_type",
        "ix_activities_source",
        "ix_activities_user_id",
    ]:
        op.drop_index(name, table_name="activities")
    op.drop_table("activities")

    for name in ["ix_integrations_status", "ix_integrations_provider", "ix_integrations_user_id"]:
        op.drop_index(name, table_name="integrations")
    op.drop_table("integrations")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    for name in ["activity_type", "activity_source", "integration_status", "integration_provider"]:
        sa.Enum(name=name).drop(bind, checkfirst=True)
