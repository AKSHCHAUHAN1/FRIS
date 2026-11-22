from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Faculty(Base, TimestampMixin):
    __tablename__ = "faculty"
    __table_args__ = (Index("ix_faculty_name_institution", "full_name", "institution"),)

    faculty_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    department: Mapped[str | None] = mapped_column(String(240))
    institution: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    institutional_email: Mapped[str | None] = mapped_column(String(320))
    orcid: Mapped[str | None] = mapped_column(String(19), index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ACTIVE", server_default="ACTIVE")

    name_variants: Mapped[list["FacultyNameVariant"]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan", lazy="selectin"
    )
    identifiers: Mapped[list["FacultyIdentifier"]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan", lazy="selectin"
    )
    publications: Mapped[list["FacultyPublication"]] = relationship(
        back_populates="faculty", cascade="all, delete-orphan"
    )
    sync_jobs: Mapped[list["SyncJob"]] = relationship(back_populates="faculty")


class FacultyNameVariant(Base):
    __tablename__ = "faculty_name_variants"
    __table_args__ = (UniqueConstraint("faculty_id", "name", name="uq_faculty_name_variant"),)

    variant_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    faculty_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("faculty.faculty_id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    faculty: Mapped[Faculty] = relationship(back_populates="name_variants")


class FacultyIdentifier(Base):
    __tablename__ = "faculty_identifiers"
    __table_args__ = (UniqueConstraint("scheme", "value", name="uq_identifier_scheme_value"),)

    identifier_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    faculty_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("faculty.faculty_id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheme: Mapped[str] = mapped_column(String(60), nullable=False)
    value: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_source: Mapped[str | None] = mapped_column(String(120))
    faculty: Mapped[Faculty] = relationship(back_populates="identifiers")


class Provider(Base):
    __tablename__ = "providers"

    provider_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    terms_url: Mapped[str | None] = mapped_column(Text)
    records: Mapped[list["ProviderRecord"]] = relationship(back_populates="provider")


class Publication(Base, TimestampMixin):
    __tablename__ = "publications"

    publication_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    doi_normalized: Mapped[str | None] = mapped_column(String(300), unique=True, index=True)
    title_normalized: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    title_display: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    publication_type: Mapped[str | None] = mapped_column(String(100), index=True)
    venue: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    canonical_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )

    provider_records: Mapped[list["ProviderRecord"]] = relationship(
        back_populates="publication", cascade="all, delete-orphan", lazy="selectin"
    )
    authorships: Mapped[list["Authorship"]] = relationship(
        back_populates="publication",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Authorship.author_position",
    )
    faculty_links: Mapped[list["FacultyPublication"]] = relationship(back_populates="publication")


class ProviderRecord(Base):
    __tablename__ = "provider_records"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_record_id", name="uq_provider_external_record"),
        Index("ix_provider_record_publication", "publication_id"),
    )

    record_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    publication_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("publications.publication_id", ondelete="CASCADE"), nullable=False
    )
    provider_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("providers.provider_id"), nullable=False)
    external_record_id: Mapped[str] = mapped_column(String(300), nullable=False)
    raw_json: Mapped[dict | None] = mapped_column(JSON)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)

    publication: Mapped[Publication] = relationship(back_populates="provider_records")
    provider: Mapped[Provider] = relationship(back_populates="records", lazy="joined")


class Authorship(Base):
    __tablename__ = "authorships"
    __table_args__ = (
        UniqueConstraint("publication_id", "author_position", name="uq_publication_author_position"),
    )

    authorship_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    publication_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("publications.publication_id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_name: Mapped[str] = mapped_column(String(300), nullable=False)
    author_position: Mapped[int] = mapped_column(Integer, nullable=False)
    external_author_id: Mapped[str | None] = mapped_column(String(300))
    affiliation_text: Mapped[str | None] = mapped_column(Text)
    publication: Mapped[Publication] = relationship(back_populates="authorships")


class FacultyPublication(Base):
    __tablename__ = "faculty_publications"
    __table_args__ = (
        UniqueConstraint("faculty_id", "publication_id", name="uq_faculty_publication"),
        Index("ix_faculty_publication_review", "match_status", "faculty_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    faculty_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("faculty.faculty_id", ondelete="CASCADE"), nullable=False
    )
    publication_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("publications.publication_id", ondelete="CASCADE"), nullable=False
    )
    match_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    match_status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    evidence_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reviewed_by: Mapped[str | None] = mapped_column(String(240))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    faculty: Mapped[Faculty] = relationship(back_populates="publications")
    publication: Mapped[Publication] = relationship(back_populates="faculty_links")


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    job_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    faculty_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("faculty.faculty_id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="QUEUED", index=True)
    request_parameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    faculty: Mapped[Faculty] = relationship(back_populates="sync_jobs")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_resource", "resource_type", "resource_id"),)

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    actor_id: Mapped[str | None] = mapped_column(String(240))
    actor_role: Mapped[str | None] = mapped_column(String(24))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
