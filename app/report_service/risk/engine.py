from statistics import mean


class RiskEngine:

    def calculate(self, findings):

        critical = 0
        high = 0
        medium = 0
        low = 0
        informational = 0

        cvss_scores = []

        for finding in findings:

            severity = finding.severity.lower()

            if severity == "critical":
                critical += 1

            elif severity == "high":
                high += 1

            elif severity == "medium":
                medium += 1

            elif severity == "low":
                low += 1

            else:
                informational += 1

            if finding.cvss_score is not None:
                cvss_scores.append(finding.cvss_score)

        average_cvss = 0

        if cvss_scores:
            average_cvss = round(mean(cvss_scores), 2)

        if critical > 0:
            overall = "Critical"

        elif high >= 3:
            overall = "High"

        elif high > 0 or medium >= 5:
            overall = "High"

        elif medium > 0:
            overall = "Medium"

        else:
            overall = "Low"

        return {

            "overall_risk": overall,

            "critical": critical,

            "high": high,

            "medium": medium,

            "low": low,

            "informational": informational,

            "average_cvss": average_cvss

        }