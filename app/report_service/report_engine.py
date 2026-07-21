from app.report_service.builders.report_builder import ReportBuilder
from app.report_service.renderer.template_renderer import TemplateRenderer
from app.report_service.pdf.pdf_renderer import PDFRenderer


class ReportEngine:

    def __init__(self, report):
        self.report = report

        self.builder = ReportBuilder(report)

        self.renderer = TemplateRenderer()

        self.pdf_renderer = PDFRenderer()

    def generate_html(self):

        print("Step 1 : Building structured report...")

        report_data = self.builder.build()

        print("✓ Structured report built")

        print("Step 2 : Rendering HTML template...")

        html = self.renderer.render(
            "base.html",
            report_data
        )

        print("✓ HTML rendered")

        return html

    def generate_pdf(self, output_path):

        html = self.generate_html()

        print("Step 3 : Generating PDF...")

        self.pdf_renderer.render_html_to_pdf(
            html,
            output_path
        )

        print("✓ PDF Generated Successfully")

        return output_path