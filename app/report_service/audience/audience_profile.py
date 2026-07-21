from dataclasses import dataclass

from app.report_service.audience.audience_type import AudienceType


@dataclass
class AudienceProfile:

    audience: AudienceType

    show_cover: bool = True

    show_dashboard: bool = True

    show_executive_summary: bool = True

    show_scope: bool = True

    show_methodology: bool = True

    show_assets: bool = True

    show_statistics: bool = True

    show_findings: bool = True

    show_evidence: bool = False

    show_http_requests: bool = False

    show_http_responses: bool = False

    show_payloads: bool = False

    show_cves: bool = False

    show_cwes: bool = False

    show_mitre: bool = False

    show_recommendations: bool = True

    show_appendix: bool = True

    show_references: bool = True

    show_compliance: bool = True

    show_screenshots: bool = False