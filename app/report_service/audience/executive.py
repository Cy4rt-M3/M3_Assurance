from .base import AudienceProfile


class ExecutiveAudience(AudienceProfile):

    name = "executive"

    def report_title(self):
        return "Executive Security Assessment Report"

    def allowed_sections(self):
        return [
            "cover",
            "dashboard",
            "executive_summary",
            "organization",
            "scope",
            "risk_matrix",
            "recommendations",
            "footer",
        ]

    def hidden_sections(self):
        return [
            "findings",
            "assets",
            "appendix",
            "references",
            "methodology",
            "compliance_mapping",
        ]