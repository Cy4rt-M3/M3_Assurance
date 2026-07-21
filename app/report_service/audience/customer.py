from .base import AudienceProfile


class CustomerAudience(AudienceProfile):

    name = "customer"

    def report_title(self):
        return "Customer Security Assessment Report"

    def allowed_sections(self):
        return [
            "cover",
            "executive_summary",
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
            "statistics",
            "methodology",
            "organization",
            "compliance_mapping",
            "dashboard",
        ]