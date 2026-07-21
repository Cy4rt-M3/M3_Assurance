from .base import AudienceProfile


class TechnicalAudience(AudienceProfile):

    name = "technical"

    def report_title(self):
        return "Technical Security Assessment Report"

    def allowed_sections(self):
        return [
            "cover",
            "dashboard",
            "executive_summary",
            "organization",
            "scope",
            "methodology",
            "assets",
            "findings",
            "statistics",
            "risk_matrix",
            "recommendations",
            "appendix",
            "references",
            "compliance_mapping",
            "footer",
        ]

    def hidden_sections(self):
        return []