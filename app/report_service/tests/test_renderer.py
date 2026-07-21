from pathlib import Path

from app.report_service.pdf.pdf_renderer import PDFRenderer
from app.report_service.models.scope import Scope

html = """
<!DOCTYPE html>

<html>

<head>

<title>Test PDF</title>

<style>

body{

font-family:Arial;

padding:40px;

}

h1{

color:#1565C0;

}

</style>

</head>

<body>

<h1>Pod Nebula</h1>

<p>If you are reading this inside a PDF then Playwright works perfectly.</p>

</body>

</html>
"""

renderer = PDFRenderer()

output = Path("sample_report.pdf")

renderer.render_html_to_pdf(
    html,
    str(output)
)

print("PDF Generated:", output.absolute())