from .base import AudienceProfile


class CISOAudience(AudienceProfile):

    name = "ciso"

    def report_title(self):
        return "Chief Information Security Officer Report"

    def allowed_sections(self):
        return [
            "cover",
            "dashboard",
            "executive_summary",
            "organization",
            "scope",
            "methodology",
            "statistics",
            "risk_matrix",
            "compliance_mapping",
            "recommendations",
            "footer",
        ]

    def hidden_sections(self):
        return [
            "appendix",
            "references",
        ]