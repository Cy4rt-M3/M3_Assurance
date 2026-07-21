from typing import Dict, Any

from app.report_service.statistics.engine import StatisticsEngine


class DashboardBuilder:

    def __init__(self, report):
        self.statistics = StatisticsEngine(report)

    def build(self):
        return self.statistics.generate()

