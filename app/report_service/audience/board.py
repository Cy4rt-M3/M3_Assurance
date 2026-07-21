from .base import AudienceProfile


class BoardAudience(AudienceProfile):

    name = "board"

    def report_title(self):
        return "Board Security Briefing"

    def allowed_sections(self):
        return [
            "cover",
            "dashboard",
            "executive_summary",
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
            "organization",
            "statistics",
            "compliance_mapping",
        ]