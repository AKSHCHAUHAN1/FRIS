"""Create the initial FRIS relational schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa
from uuid import UUID

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "providers",
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("terms_url", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("provider_id"),
        sa.UniqueConstraint("provider_name"),
    )
    op.create_table(
        "faculty",
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=240), nullable=False),
        sa.Column("department", sa.String(length=240), nullable=True),
        sa.Column("institution", sa.String(length=300), nullable=False),
        sa.Column("institutional_email", sa.String(length=320), nullable=True),
        sa.Column("orcid", sa.String(length=19), nullable=True),
        sa.Column("status", sa.String(length=24), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("faculty_id"),
    )
    op.create_index("ix_faculty_full_name", "faculty", ["full_name"])
    op.create_index("ix_faculty_institution", "faculty", ["institution"])
    op.create_index("ix_faculty_orcid", "faculty", ["orcid"])
    op.create_index("ix_faculty_name_institution", "faculty", ["full_name", "institution"])

    op.create_table(
        "faculty_name_variants",
        sa.Column("variant_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.faculty_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("variant_id"),
        sa.UniqueConstraint("faculty_id", "name", name="uq_faculty_name_variant"),
    )
    op.create_index("ix_faculty_name_variants_faculty_id", "faculty_name_variants", ["faculty_id"])

    op.create_table(
        "faculty_identifiers",
        sa.Column("identifier_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("scheme", sa.String(length=60), nullable=False),
        sa.Column("value", sa.String(length=240), nullable=False),
        sa.Column("verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_source", sa.String(length=120), nullable=True),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.faculty_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("identifier_id"),
        sa.UniqueConstraint("scheme", "value", name="uq_identifier_scheme_value"),
    )
    op.create_index("ix_faculty_identifiers_faculty_id", "faculty_identifiers", ["faculty_id"])
    op.create_index("ix_faculty_identifiers_value", "faculty_identifiers", ["value"])

    op.create_table(
        "publications",
        sa.Column("publication_id", sa.Uuid(), nullable=False),
        sa.Column("doi_normalized", sa.String(length=300), nullable=True),
        sa.Column("title_normalized", sa.Text(), nullable=False),
        sa.Column("title_display", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("publication_type", sa.String(length=100), nullable=True),
        sa.Column("venue", sa.Text(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("canonical_status", sa.String(length=24), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("publication_id"),
    )
    op.create_index("ix_publications_doi_normalized", "publications", ["doi_normalized"], unique=True)
    op.create_index("ix_publications_title_normalized", "publications", ["title_normalized"])
    op.create_index("ix_publications_year", "publications", ["year"])
    op.create_index("ix_publications_publication_type", "publications", ["publication_type"])

    op.create_table(
        "provider_records",
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("publication_id", sa.Uuid(), nullable=False),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("external_record_id", sa.String(length=300), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["publication_id"], ["publications.publication_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.provider_id"]),
        sa.PrimaryKeyConstraint("record_id"),
        sa.UniqueConstraint("provider_id", "external_record_id", name="uq_provider_external_record"),
    )
    op.create_index("ix_provider_record_publication", "provider_records", ["publication_id"])

    op.create_table(
        "authorships",
        sa.Column("authorship_id", sa.Uuid(), nullable=False),
        sa.Column("publication_id", sa.Uuid(), nullable=False),
        sa.Column("author_name", sa.String(length=300), nullable=False),
        sa.Column("author_position", sa.Integer(), nullable=False),
        sa.Column("external_author_id", sa.String(length=300), nullable=True),
        sa.Column("affiliation_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["publication_id"], ["publications.publication_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("authorship_id"),
        sa.UniqueConstraint("publication_id", "author_position", name="uq_publication_author_position"),
    )
    op.create_index("ix_authorships_publication_id", "authorships", ["publication_id"])

    op.create_table(
        "faculty_publications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("publication_id", sa.Uuid(), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("match_status", sa.String(length=24), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("reviewed_by", sa.String(length=240), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.faculty_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["publication_id"], ["publications.publication_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("faculty_id", "publication_id", name="uq_faculty_publication"),
    )
    op.create_index("ix_faculty_publications_match_status", "faculty_publications", ["match_status"])
    op.create_index("ix_faculty_publication_review", "faculty_publications", ["match_status", "faculty_id"])

    op.create_table(
        "sync_jobs",
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("request_parameters", sa.JSON(), nullable=False),
        sa.Column("source_summary", sa.JSON(), nullable=False),
        sa.Column("error_summary", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["faculty_id"], ["faculty.faculty_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_sync_jobs_faculty_id", "sync_jobs", ["faculty_id"])
    op.create_index("ix_sync_jobs_status", "sync_jobs", ["status"])

    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.String(length=240), nullable=True),
        sa.Column("actor_role", sa.String(length=24), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_audit_resource", "audit_events", ["resource_type", "resource_id"])

    providers = sa.table(
        "providers",
        sa.column("provider_id", sa.Uuid()),
        sa.column("provider_name", sa.String()),
        sa.column("enabled", sa.Boolean()),
    )
    op.bulk_insert(
        providers,
        [
            {"provider_id": UUID("00000000-0000-4000-8000-000000000001"), "provider_name": "OpenAlex", "enabled": True},
            {"provider_id": UUID("00000000-0000-4000-8000-000000000002"), "provider_name": "Crossref", "enabled": True},
            {"provider_id": UUID("00000000-0000-4000-8000-000000000003"), "provider_name": "Semantic Scholar", "enabled": True},
            {"provider_id": UUID("00000000-0000-4000-8000-000000000004"), "provider_name": "ORCID", "enabled": True},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_resource", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_sync_jobs_status", table_name="sync_jobs")
    op.drop_index("ix_sync_jobs_faculty_id", table_name="sync_jobs")
    op.drop_table("sync_jobs")
    op.drop_index("ix_faculty_publication_review", table_name="faculty_publications")
    op.drop_index("ix_faculty_publications_match_status", table_name="faculty_publications")
    op.drop_table("faculty_publications")
    op.drop_index("ix_authorships_publication_id", table_name="authorships")
    op.drop_table("authorships")
    op.drop_index("ix_provider_record_publication", table_name="provider_records")
    op.drop_table("provider_records")
    op.drop_index("ix_publications_publication_type", table_name="publications")
    op.drop_index("ix_publications_year", table_name="publications")
    op.drop_index("ix_publications_title_normalized", table_name="publications")
    op.drop_index("ix_publications_doi_normalized", table_name="publications")
    op.drop_table("publications")
    op.drop_table("faculty_identifiers")
    op.drop_table("faculty_name_variants")
    op.drop_index("ix_faculty_name_institution", table_name="faculty")
    op.drop_index("ix_faculty_orcid", table_name="faculty")
    op.drop_index("ix_faculty_institution", table_name="faculty")
    op.drop_index("ix_faculty_full_name", table_name="faculty")
    op.drop_table("faculty")
    op.drop_table("providers")
