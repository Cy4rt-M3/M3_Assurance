from pathlib import Path
from tempfile import NamedTemporaryFile

from playwright.sync_api import sync_playwright


class PDFRenderer:

    def __init__(self):

        self.page_format = "A4"

        self.margin = {
            "top": "20mm",
            "bottom": "20mm",
            "left": "15mm",
            "right": "15mm"
        }

    def render_html_to_pdf(
            self,
            html: str,
            output_pdf: str
    ):
        from pathlib import Path

        temp_html = Path("tests/reports/debug_report.html").resolve()

        temp_html.parent.mkdir(parents=True, exist_ok=True)

        temp_html.write_text(
            html,
            encoding="utf-8"
        )

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page()

            page.goto(
                temp_html.as_uri(),
                wait_until="networkidle"
            )

            page.pdf(
                path=output_pdf,
                format=self.page_format,
                print_background=True,
                margin=self.margin
            )

            browser.close()

         # temp_html.unlink(missing_ok=True)