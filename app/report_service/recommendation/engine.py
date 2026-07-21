from typing import List


class RecommendationEngine:

    def __init__(self, findings):
        self.findings = findings

    def generate(self):

        recommendations = []

        for finding in self.findings:

            severity = finding.severity.lower()

            if severity == "critical":

                recommendations.append({

                    "priority": 1,

                    "title": "Immediate Remediation Required",

                    "description":
                        "Resolve this Critical vulnerability immediately."

                })

            elif severity == "high":

                recommendations.append({

                    "priority": 2,

                    "title": "High Risk Remediation",

                    "description":
                        "Patch this High severity vulnerability as soon as possible."

                })

            elif severity == "medium":

                recommendations.append({

                    "priority": 3,

                    "title": "Medium Risk Remediation",

                    "description":
                        "Schedule remediation during the next maintenance window."

                })

            elif severity == "low":

                recommendations.append({

                    "priority": 4,

                    "title": "Low Risk Improvement",

                    "description":
                        "Address this issue as part of routine security improvements."

                })

        return recommendations