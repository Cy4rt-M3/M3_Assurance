from app.report_service.audience.audience_profile import AudienceProfile
from app.report_service.audience.audience_type import AudienceType


class AudienceFilter:

    @staticmethod
    def executive():

        return AudienceProfile(

            audience=AudienceType.EXECUTIVE,

            show_http_requests=False,

            show_http_responses=False,

            show_payloads=False,

            show_evidence=False,

            show_cves=False,

            show_cwes=False,

            show_mitre=False,

            show_screenshots=False

        )

    @staticmethod
    def ciso():

        return AudienceProfile(

            audience=AudienceType.CISO,

            show_http_requests=False,

            show_http_responses=False,

            show_payloads=False,

            show_evidence=True,

            show_cves=True,

            show_cwes=True,

            show_mitre=True,

            show_screenshots=True

        )

    @staticmethod
    def technical():

        return AudienceProfile(

            audience=AudienceType.TECHNICAL,

            show_http_requests=True,

            show_http_responses=True,

            show_payloads=True,

            show_evidence=True,

            show_cves=True,

            show_cwes=True,

            show_mitre=True,

            show_screenshots=True

        )