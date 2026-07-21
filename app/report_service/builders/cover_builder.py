"""
cover_builder.py

Builds the Cover Page section for the security assessment report.

This module is responsible for extracting and normalizing only the
data required to render the first page of a report (title, organization
metadata, classification markings, and issuance details). It performs
no formatting/rendering itself -- that is the responsibility of the
template layer -- but it guarantees a complete, well-typed payload so
templates never have to guard against missing keys.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, TypedDict

from app.report_service.models.report import Report, Organization

logger = logging.getLogger(__name__)

__all__ = ["CoverBuilder", "CoverPageData", "Classification", "CoverBuilderError"]


class CoverBuilderError(Exception):
    """Raised when a report cannot produce a valid cover page payload."""


class Classification(str, Enum):
    """Standard document sensitivity markings."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


DEFAULT_CLASSIFICATION = Classification.CONFIDENTIAL
DEFAULT_REPORT_VERSION = "1.0"
DEFAULT_PREPARED_BY = "CYART Offensive Security Team"
DATE_FORMAT = "%Y-%m-%d %H:%M %Z"


class CoverPageData(TypedDict):
    """Typed contract for the cover page payload consumed by templates."""

    report_id: str
    title: str
    organization_name: str
    industry: Optional[str]
    website: Optional[str]
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    country: Optional[str]
    city: Optional[str]
    generated_at: str
    classification: str
    version: str
    prepared_by: str


@dataclass(frozen=True)
class CoverBuilder:
    """
    Builds the data payload for a report's cover page.

    Extracts only the fields required for the first page of the report,
    applying safe defaults and normalization so the template layer can
    render without additional null-checking.

    Args:
        report: The source report aggregate containing organization and
            metadata required to populate the cover page.

    Raises:
        CoverBuilderError: If mandatory identifying fields (report_id,
            title, or organization) are missing from the report.
    """

    report: Report

    def build(self) -> CoverPageData:
        """Build and return the normalized cover page payload."""
        self._validate()
        organization = self.report.organization

        return CoverPageData(
            report_id=self.report.report_id,
            title=self.report.title,
            organization_name=organization.name,
            industry=self._safe_str(organization.industry),
            website=self._safe_str(organization.website),
            contact_person=self._safe_str(organization.contact_person),
            email=self._safe_str(organization.email),
            phone=self._safe_str(organization.phone),
            country=self._safe_str(organization.country),
            city=self._safe_str(organization.city),
            generated_at=self._format_timestamp(self.report.generated_at),
            classification=self._resolve_classification().value,
            version=getattr(self.report, "version", DEFAULT_REPORT_VERSION),
            prepared_by=getattr(self.report, "prepared_by", DEFAULT_PREPARED_BY),
        )

    def _validate(self) -> None:
        """Ensure mandatory identifying fields are present before building."""
        missing = [
            field
            for field, value in (
                ("report_id", getattr(self.report, "report_id", None)),
                ("title", getattr(self.report, "title", None)),
                ("organization", getattr(self.report, "organization", None)),
            )
            if not value
        ]
        if missing:
            raise CoverBuilderError(
                f"Cannot build cover page: missing required field(s) {missing} "
                f"on report."
            )

    def _resolve_classification(self) -> Classification:
        """Resolve the report's classification, falling back to the default."""
        raw_value = getattr(self.report, "classification", None)
        if raw_value is None:
            return DEFAULT_CLASSIFICATION
        try:
            return Classification(str(raw_value).upper())
        except ValueError:
            logger.warning(
                "Unrecognized classification %r on report %s; defaulting to %s",
                raw_value,
                getattr(self.report, "report_id", "unknown"),
                DEFAULT_CLASSIFICATION.value,
            )
            return DEFAULT_CLASSIFICATION

    @staticmethod
    def _format_timestamp(value: Any) -> str:
        """Normalize a datetime (or datetime-like value) to a display string."""
        if isinstance(value, datetime):
            return value.strftime(DATE_FORMAT).strip()
        if value:
            return str(value)
        logger.warning("Report generated_at missing; using current UTC time.")
        return datetime.utcnow().strftime(DATE_FORMAT).strip()

    @staticmethod
    def _safe_str(value: Any) -> Optional[str]:
        """Coerce optional organization fields to str, preserving None."""
        return str(value) if value is not None else None