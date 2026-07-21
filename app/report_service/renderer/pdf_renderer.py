"""
pdf_report_renderer.py

Renders a fully-formatted, presentation-grade PDF security assessment
report from the plain-dict structure produced by
`app.report_service.builders.report_builder.ReportBuilder.build()`.

This module is intentionally decoupled from the domain models (Report,
Organization, Asset, Finding, ...): it consumes only the JSON-serializable
dict that ReportBuilder already produces. That keeps "assemble the data"
and "lay out the document" as two independently testable concerns, and
means this renderer works unchanged even if the domain models change.

Layout conventions follow what you'd see in a professional third-party
security assessment report (Big 4 / boutique pentest firm style):

  - Cover page with classification banner
  - Document control / revision history
  - Auto-generated table of contents with real page numbers
  - Executive summary with a severity-distribution chart
  - A single, consistent severity color taxonomy used everywhere
  - Scope & methodology
  - Asset inventory
  - Risk matrix
  - One detailed write-up per finding, with a CVSS gauge
  - Prioritized recommendations
  - Compliance mapping matrix
  - Appendix & references
  - Running header + footer with "Page X of Y" and confidentiality marking
    on every content page

Usage:
    from pdf_report_renderer import render_report_pdf
    render_report_pdf(report_data, "output.pdf")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Rect, String, Line

logger = logging.getLogger(__name__)


# =====================================================
# BRAND / DESIGN TOKENS
# =====================================================

@dataclass(frozen=True)
class Theme:
    """Single source of truth for the report's visual identity.

    Centralizing this means the whole document is re-themed by editing
    one object, instead of hunting hex codes through the layout code.
    """

    primary: str = "#0B2545"       # deep navy - headers, cover
    accent: str = "#1E6FD9"        # accent blue - links, highlights
    ink: str = "#1A1A1A"           # body text
    muted: str = "#5B6472"         # secondary text
    hairline: str = "#D8DCE3"      # rules / table borders
    panel_bg: str = "#F4F6F9"      # light section backgrounds

    critical: str = "#B3021A"
    high: str = "#D9480F"
    medium: str = "#E8A700"
    low: str = "#2F9E44"
    informational: str = "#4263A6"

    font_body: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"

    page_size = A4
    margin_top: float = 2.4 * cm
    margin_bottom: float = 2.0 * cm
    margin_side: float = 2.0 * cm


THEME = Theme()

SEVERITY_ORDER = ["critical", "high", "medium", "low", "informational"]

SEVERITY_LABELS = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "informational": "Informational",
}


def severity_color(severity: str) -> HexColor:
    key = (severity or "").strip().lower()
    hex_value = getattr(THEME, key, THEME.muted)
    return HexColor(hex_value)


def normalize_severity(severity: str) -> str:
    key = (severity or "").strip().lower()
    return key if key in SEVERITY_ORDER else "informational"


# =====================================================
# STYLESHEET
# =====================================================

def build_stylesheet() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: Dict[str, ParagraphStyle] = {}

    styles["CoverTitle"] = ParagraphStyle(
        "CoverTitle", parent=base["Title"],
        fontName=THEME.font_bold, fontSize=28, leading=34,
        textColor=colors.white, alignment=TA_LEFT, spaceAfter=6,
    )
    styles["CoverSubtitle"] = ParagraphStyle(
        "CoverSubtitle", parent=base["Normal"],
        fontName=THEME.font_body, fontSize=13, leading=18,
        textColor=HexColor("#C9D6E8"), alignment=TA_LEFT,
    )
    styles["CoverMeta"] = ParagraphStyle(
        "CoverMeta", parent=base["Normal"],
        fontName=THEME.font_body, fontSize=10.5, leading=15,
        textColor=colors.white, alignment=TA_LEFT,
    )
    styles["ClassificationBanner"] = ParagraphStyle(
        "ClassificationBanner", parent=base["Normal"],
        fontName=THEME.font_bold, fontSize=11, leading=14,
        textColor=colors.white, alignment=TA_CENTER,
    )

    styles["SectionHeading"] = ParagraphStyle(
        "SectionHeading", parent=base["Heading1"],
        fontName=THEME.font_bold, fontSize=17, leading=21,
        textColor=HexColor(THEME.primary), spaceBefore=4, spaceAfter=10,
        borderPadding=0,
    )
    styles["SubHeading"] = ParagraphStyle(
        "SubHeading", parent=base["Heading2"],
        fontName=THEME.font_bold, fontSize=12.5, leading=16,
        textColor=HexColor(THEME.primary), spaceBefore=10, spaceAfter=6,
    )
    styles["FindingTitle"] = ParagraphStyle(
        "FindingTitle", parent=base["Heading2"],
        fontName=THEME.font_bold, fontSize=13, leading=16,
        textColor=HexColor(THEME.ink), spaceBefore=0, spaceAfter=2,
    )

    styles["Body"] = ParagraphStyle(
        "Body", parent=base["Normal"],
        fontName=THEME.font_body, fontSize=9.7, leading=14.5,
        textColor=HexColor(THEME.ink), alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    styles["BodyMuted"] = ParagraphStyle(
        "BodyMuted", parent=base["Normal"],
        fontName=THEME.font_body, fontSize=9, leading=13,
        textColor=HexColor(THEME.muted),
    )
    styles["Label"] = ParagraphStyle(
        "Label", parent=base["Normal"],
        fontName=THEME.font_bold, fontSize=8.3, leading=11,
        textColor=HexColor(THEME.muted),
    )
    styles["TableCell"] = ParagraphStyle(
        "TableCell", parent=base["Normal"],
        fontName=THEME.font_body, fontSize=8.6, leading=11.5,
        textColor=HexColor(THEME.ink),
    )
    styles["TableCellHeader"] = ParagraphStyle(
        "TableCellHeader", parent=base["Normal"],
        fontName=THEME.font_bold, fontSize=8.6, leading=11.5,
        textColor=colors.white,
    )
    styles["TOCHeading"] = ParagraphStyle(
        "TOCHeading", parent=base["Heading1"],
        fontName=THEME.font_bold, fontSize=17, leading=21,
        textColor=HexColor(THEME.primary), spaceAfter=14,
    )
    styles["ExecSummaryStat"] = ParagraphStyle(
        "ExecSummaryStat", parent=base["Normal"],
        fontName=THEME.font_bold, fontSize=20, leading=22,
        alignment=TA_CENTER, textColor=colors.white,
    )
    styles["ExecSummaryStatLabel"] = ParagraphStyle(
        "ExecSummaryStatLabel", parent=base["Normal"],
        fontName=THEME.font_body, fontSize=8, leading=10,
        alignment=TA_CENTER, textColor=colors.white,
    )

    return styles


# =====================================================
# LOW-LEVEL DRAWING HELPERS (charts / gauges / badges)
# =====================================================

def severity_distribution_chart(stats: Dict[str, Any], width: float = 460, height: float = 150) -> Drawing:
    """Horizontal bar chart of finding counts per severity, hand-drawn so
    every bar gets the exact brand color for its severity (rather than
    fighting reportlab's chart-level color-cycling API)."""

    d = Drawing(width, height)
    counts = {s: int(stats.get(s, 0) or 0) for s in SEVERITY_ORDER}
    max_count = max(counts.values()) or 1

    row_h = height / len(SEVERITY_ORDER)
    label_w = 92
    bar_area_w = width - label_w - 46
    left = label_w

    for i, sev in enumerate(SEVERITY_ORDER):
        y = height - (i + 1) * row_h + row_h * 0.28
        count = counts[sev]
        bar_w = (count / max_count) * bar_area_w if max_count else 0

        d.add(String(0, y + row_h * 0.12, SEVERITY_LABELS[sev],
                      fontName=THEME.font_body, fontSize=9, fillColor=HexColor(THEME.ink)))
        d.add(Rect(left, y, bar_area_w, row_h * 0.44,
                    fillColor=HexColor(THEME.panel_bg), strokeColor=None))
        if bar_w > 0:
            d.add(Rect(left, y, bar_w, row_h * 0.44,
                        fillColor=severity_color(sev), strokeColor=None))
        d.add(String(left + bar_area_w + 8, y + row_h * 0.12, str(count),
                      fontName=THEME.font_bold, fontSize=9.5, fillColor=HexColor(THEME.ink)))

    return d


def cvss_gauge(score: float, width: float = 130, height: float = 16) -> Drawing:
    """Small inline 0-10 CVSS scale gauge, filled proportionally and
    colored to match the finding's severity band."""

    score = max(0.0, min(10.0, float(score or 0)))
    d = Drawing(width, height)

    d.add(Rect(0, height * 0.28, width, height * 0.44,
                fillColor=HexColor(THEME.panel_bg), strokeColor=HexColor(THEME.hairline), strokeWidth=0.5))

    if score >= 9.0:
        band_color = THEME.critical
    elif score >= 7.0:
        band_color = THEME.high
    elif score >= 4.0:
        band_color = THEME.medium
    elif score > 0.0:
        band_color = THEME.low
    else:
        band_color = THEME.informational

    fill_w = (score / 10.0) * width
    if fill_w > 0:
        d.add(Rect(0, height * 0.28, fill_w, height * 0.44,
                    fillColor=HexColor(band_color), strokeColor=None))

    d.add(String(width + 6, height * 0.3, f"{score:.1f}",
                  fontName=THEME.font_bold, fontSize=9.5, fillColor=HexColor(THEME.ink)))
    return d


def severity_badge_table(severity: str) -> Table:
    """A small filled, rounded-look pill badge used next to finding titles."""
    label = SEVERITY_LABELS[normalize_severity(severity)]
    t = Table([[label]], colWidths=[1.9 * cm], rowHeights=[0.55 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), severity_color(severity)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), THEME.font_bold),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# =====================================================
# DOC TEMPLATE (TOC support + numbered pages)
# =====================================================

class NumberedCanvas(pdfcanvas.Canvas):
    """Buffers pages so the footer can print 'Page X of Y' — the total
    page count isn't known until every page has been laid out."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[dict] = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if not getattr(self, "_is_cover_page", False):
                self._draw_page_number(total_pages)
            super().showPage()
        super().save()

    def _draw_page_number(self, total_pages: int) -> None:
        self.setFont(THEME.font_body, 8.3)
        self.setFillColor(HexColor(THEME.muted))
        text = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(THEME.page_size[0] - THEME.margin_side, 1.15 * cm, text)


class ReportDocTemplate(BaseDocTemplate):
    """BaseDocTemplate that feeds SectionHeading/SubHeading paragraphs into
    the TableOfContents as they're laid out, so the TOC has real,
    post-layout page numbers rather than guessed ones."""

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        text = flowable.getPlainText()
        if style_name == "SectionHeading":
            self.notify("TOCEntry", (0, text, self.page))
            key = f"h1-{self.page}-{text}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0, closed=False)
        elif style_name == "SubHeading":
            self.notify("TOCEntry", (1, text, self.page))


def _header_footer_content(canvas_obj: pdfcanvas.Canvas, doc: BaseDocTemplate, report_title: str) -> None:
    canvas_obj._is_cover_page = False
    canvas_obj.saveState()

    width, height = THEME.page_size

    # Header rule + running title
    canvas_obj.setStrokeColor(HexColor(THEME.hairline))
    canvas_obj.setLineWidth(0.6)
    canvas_obj.line(THEME.margin_side, height - 1.5 * cm, width - THEME.margin_side, height - 1.5 * cm)

    canvas_obj.setFont(THEME.font_bold, 8.5)
    canvas_obj.setFillColor(HexColor(THEME.primary))
    canvas_obj.drawString(THEME.margin_side, height - 1.3 * cm, report_title)

    canvas_obj.setFont(THEME.font_bold, 8.5)
    canvas_obj.setFillColor(HexColor(THEME.critical))
    canvas_obj.drawRightString(width - THEME.margin_side, height - 1.3 * cm, "CONFIDENTIAL")

    # Footer rule + confidentiality note (page number added later by NumberedCanvas)
    canvas_obj.setStrokeColor(HexColor(THEME.hairline))
    canvas_obj.line(THEME.margin_side, 1.5 * cm, width - THEME.margin_side, 1.5 * cm)

    canvas_obj.setFont(THEME.font_body, 8.3)
    canvas_obj.setFillColor(HexColor(THEME.muted))
    canvas_obj.drawString(THEME.margin_side, 1.15 * cm, "This document contains confidential information.")

    canvas_obj.restoreState()


def _cover_page_decoration(canvas_obj: pdfcanvas.Canvas, doc: BaseDocTemplate) -> None:
    canvas_obj._is_cover_page = True


def _cover_page_background(canvas_obj: pdfcanvas.Canvas, doc: BaseDocTemplate) -> None:
    """Full-bleed navy background + classification banner for the cover."""
    canvas_obj._is_cover_page = True
    canvas_obj.saveState()
    width, height = THEME.page_size

    canvas_obj.setFillColor(HexColor(THEME.primary))
    canvas_obj.rect(0, 0, width, height, fill=1, stroke=0)

    # Accent stripe
    canvas_obj.setFillColor(HexColor(THEME.accent))
    canvas_obj.rect(0, height - 0.35 * cm, width, 0.35 * cm, fill=1, stroke=0)

    # Classification banner (top)
    canvas_obj.setFillColor(HexColor(THEME.critical))
    canvas_obj.rect(0, height - 1.9 * cm, width, 0.95 * cm, fill=1, stroke=0)
    canvas_obj.setFont(THEME.font_bold, 11)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.drawCentredString(width / 2, height - 1.6 * cm, "CONFIDENTIAL \u2014 FOR AUTHORIZED DISTRIBUTION ONLY")

    # Classification banner (bottom, mirrored)
    canvas_obj.setFillColor(HexColor(THEME.critical))
    canvas_obj.rect(0, 1.1 * cm, width, 0.7 * cm, fill=1, stroke=0)
    canvas_obj.setFont(THEME.font_bold, 8.5)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.drawCentredString(width / 2, 1.32 * cm, "CONFIDENTIAL")

    canvas_obj.restoreState()


# =====================================================
# SECTION BUILDERS
# =====================================================

def _kv_table(rows: List[List[str]], styles: Dict[str, ParagraphStyle],
              label_width: float = 4.2 * cm, value_width: float = 11.3 * cm) -> Table:
    data = [
        [Paragraph(str(label), styles["Label"]), Paragraph(str(value), styles["Body"])]
        for label, value in rows
    ]
    t = Table(data, colWidths=[label_width, value_width])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, HexColor(THEME.hairline)),
    ]))
    return t


def build_cover(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    cover = data["cover"]
    org = data["organization"]
    scope = data["scope"]

    generated_at = cover.get("generated_at")
    if isinstance(generated_at, datetime):
        generated_str = generated_at.strftime("%d %B %Y")
    else:
        generated_str = str(generated_at) if generated_at else datetime.now().strftime("%d %B %Y")

    story.append(Spacer(1, 6.8 * cm))
    story.append(Paragraph(cover.get("title", "Security Assessment Report"), styles["CoverTitle"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(scope.get("assessment_type", ""), styles["CoverSubtitle"]))
    story.append(Spacer(1, 2.2 * cm))

    meta_rows = [
        ("Prepared For", org.get("name", "")),
        ("Report ID", cover.get("report_id", "")),
        ("Assessment Period", scope.get("assessment_period", "")),
        ("Assessment Team", scope.get("assessment_team", "")),
        ("Date Issued", generated_str),
    ]
    for label, value in meta_rows:
        story.append(Paragraph(f'<font color="#9FB3D1">{label}:</font> {value}', styles["CoverMeta"]))
        story.append(Spacer(1, 3))

    story.append(NextPageTemplate("standard"))
    story.append(PageBreak())


def build_document_control(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    appendix = data["appendix"]
    generated_at = data["cover"].get("generated_at")
    date_str = generated_at.strftime("%d %b %Y") if isinstance(generated_at, datetime) else str(generated_at)

    story.append(Paragraph("Document Control", styles["SectionHeading"]))
    story.append(Paragraph(
        "This document is classified according to the sensitivity of its contents and is intended "
        "solely for the recipient organization identified on the cover page.",
        styles["Body"]))
    story.append(Spacer(1, 8))

    header = ["Version", "Date", "Author", "Description", "Classification"]
    rows = [header, [
        appendix.get("report_version", "1.0"),
        date_str,
        "CYART Offensive Security Team",
        "Initial release",
        appendix.get("classification", "Confidential"),
    ]]
    table_data = [
        [Paragraph(c, styles["TableCellHeader"]) if r == 0 else Paragraph(str(c), styles["TableCell"])
         for c in row]
        for r, row in enumerate(rows)
    ]
    t = Table(table_data, colWidths=[2.1 * cm, 2.6 * cm, 4.6 * cm, 4.6 * cm, 2.7 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(THEME.primary)),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor(THEME.hairline)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor(THEME.panel_bg)]),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Distribution List", styles["SubHeading"]))
    org = data["organization"]
    story.append(_kv_table([
        ("Organization", org.get("name", "")),
        ("Contact", org.get("contact_person", "")),
        ("Email", org.get("email", "")),
    ], styles))
    story.append(PageBreak())


def build_toc(story: List, styles: Dict[str, ParagraphStyle]) -> None:
    story.append(Paragraph("Table of Contents", styles["TOCHeading"]))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(name="TOCLevel0", fontName=THEME.font_bold, fontSize=10.5,
                        leading=16, textColor=HexColor(THEME.ink)),
        ParagraphStyle(name="TOCLevel1", fontName=THEME.font_body, fontSize=9.5,
                        leading=14, leftIndent=14, textColor=HexColor(THEME.muted)),
    ]
    story.append(toc)
    story.append(PageBreak())


def build_executive_summary(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    stats = data["statistics"]
    exec_summary = data["executive_summary"]

    story.append(Paragraph("Executive Summary", styles["SectionHeading"]))
    story.append(Paragraph(exec_summary["summary_text"], styles["Body"]))
    story.append(Spacer(1, 10))

    # Overall risk banner
    overall_risk = str(exec_summary.get("overall_risk", "Unknown"))
    banner_color = severity_color(overall_risk)
    banner = Table([[Paragraph(f"OVERALL ORGANIZATIONAL RISK: {overall_risk.upper()}",
                                 styles["ClassificationBanner"])]], colWidths=[16.9 * cm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), banner_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(banner)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Findings by Severity", styles["SubHeading"]))
    story.append(severity_distribution_chart(stats))
    story.append(Spacer(1, 6))

    avg_cvss = stats.get("average_cvss", "N/A")
    total_findings = sum(int(stats.get(s, 0) or 0) for s in SEVERITY_ORDER)
    stat_cells = [
        ("Total Findings", str(total_findings)),
        ("Average CVSS", str(avg_cvss)),
        ("Critical + High", str(int(stats.get("critical", 0) or 0) + int(stats.get("high", 0) or 0))),
        ("Assets in Scope", str(len(data.get("assets", [])))),
    ]
    row = []
    for label, value in stat_cells:
        cell = Table(
            [[Paragraph(value, styles["ExecSummaryStat"])],
             [Paragraph(label.upper(), styles["ExecSummaryStatLabel"])]],
            colWidths=[4.0 * cm],
        )
        cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(THEME.primary)),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        row.append(cell)
    spacer_table = Table([row], colWidths=None, spaceBefore=4)
    spacer_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(spacer_table)
    story.append(PageBreak())


def build_scope_and_methodology(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    scope = data["scope"]
    methodology = data["methodology"]

    story.append(Paragraph("Scope & Methodology", styles["SectionHeading"]))
    story.append(Paragraph("Assessment Scope", styles["SubHeading"]))
    story.append(_kv_table([
        ("Assessment Name", scope.get("assessment_name", "")),
        ("Assessment Type", scope.get("assessment_type", "")),
        ("Target", scope.get("target", "")),
        ("Assessment Period", scope.get("assessment_period", "")),
        ("Assessment Team", scope.get("assessment_team", "")),
        ("Framework", scope.get("framework", "")),
        ("Testing Type", scope.get("testing_type", "")),
    ], styles))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Methodology", styles["SubHeading"]))
    story.append(Paragraph(
        "The assessment was conducted in accordance with the phases below, "
        "combining automated tooling with manual validation to minimize "
        "false positives and confirm real-world exploitability.",
        styles["Body"]))
    story.append(Spacer(1, 6))

    phase_rows = [[Paragraph(f"{i+1}. {phase}", styles["TableCell"])]
                  for i, phase in enumerate(methodology.keys())]
    t = Table(phase_rows, colWidths=[16.9 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor(THEME.hairline)),
        ("BACKGROUND", (0, 0), (-1, -1), HexColor(THEME.panel_bg)),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    story.append(PageBreak())


def build_asset_inventory(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    assets = data["assets"]
    story.append(Paragraph("Asset Inventory", styles["SectionHeading"]))
    story.append(Paragraph(
        f"{len(assets)} asset(s) were included within the scope of this assessment.",
        styles["Body"]))
    story.append(Spacer(1, 8))

    header = ["Hostname", "IP Address", "Type", "OS", "Environment", "Criticality", "Owner"]
    table_data = [[Paragraph(h, styles["TableCellHeader"]) for h in header]]
    for asset in assets:
        table_data.append([
            Paragraph(str(asset.get("hostname", "")), styles["TableCell"]),
            Paragraph(str(asset.get("ip_address", "")), styles["TableCell"]),
            Paragraph(str(asset.get("asset_type", "")), styles["TableCell"]),
            Paragraph(str(asset.get("operating_system", "")), styles["TableCell"]),
            Paragraph(str(asset.get("environment", "")), styles["TableCell"]),
            Paragraph(str(asset.get("criticality", "")), styles["TableCell"]),
            Paragraph(str(asset.get("owner", "")), styles["TableCell"]),
        ])

    t = Table(table_data, colWidths=[2.7 * cm, 2.6 * cm, 2.4 * cm, 3.0 * cm, 2.3 * cm, 2.1 * cm, 1.8 * cm],
               repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(THEME.primary)),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor(THEME.hairline)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor(THEME.panel_bg)]),
    ]))
    story.append(t)
    story.append(PageBreak())


def build_risk_matrix(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    matrix = data["risk_matrix"]
    story.append(Paragraph("Risk Matrix", styles["SectionHeading"]))
    story.append(Paragraph(
        "The table below summarizes the number of findings identified per "
        "severity classification.", styles["Body"]))
    story.append(Spacer(1, 8))

    header = [Paragraph(SEVERITY_LABELS[s], styles["TableCellHeader"]) for s in SEVERITY_ORDER]
    values = [Paragraph(str(matrix.get(SEVERITY_LABELS[s], matrix.get(s, 0))), styles["TableCellHeader"])
              for s in SEVERITY_ORDER]

    t = Table([header, values], colWidths=[16.9 * cm / 5] * 5)
    row_colors = [severity_color(s) for s in SEVERITY_ORDER]
    style_cmds = [
        ("GRID", (0, 0), (-1, -1), 0.6, colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]
    for i, c in enumerate(row_colors):
        style_cmds.append(("BACKGROUND", (i, 0), (i, 0), c))
        style_cmds.append(("BACKGROUND", (i, 1), (i, 1), HexColor(THEME.panel_bg)))
        style_cmds.append(("TEXTCOLOR", (i, 1), (i, 1), HexColor(THEME.ink)))
    t.setStyle(TableStyle(style_cmds))
    story.append(t)
    story.append(PageBreak())


def build_findings(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    findings = data["findings"]
    story.append(Paragraph("Detailed Findings", styles["SectionHeading"]))
    story.append(Paragraph(
        f"This section documents all {len(findings)} finding(s) identified during the "
        "assessment, ordered by severity, along with recommended remediation.",
        styles["Body"]))
    story.append(Spacer(1, 10))

    severity_rank = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    ordered = sorted(findings, key=lambda f: severity_rank.get(normalize_severity(f.get("severity", "")), 99))

    for finding in ordered:
        block: List = []
        title_row = Table(
            [[Paragraph(f"{finding.get('finding_id', '')}: {finding.get('title', '')}", styles["FindingTitle"]),
              severity_badge_table(finding.get("severity", ""))]],
            colWidths=[14.6 * cm, 2.3 * cm],
        )
        title_row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))
        block.append(title_row)
        block.append(Spacer(1, 4))

        cvss_row = Table(
            [[Paragraph("CVSS Score", styles["Label"]), cvss_gauge(finding.get("cvss_score", 0))]],
            colWidths=[3.0 * cm, 5.0 * cm],
        )
        cvss_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        block.append(cvss_row)
        block.append(Spacer(1, 6))

        block.append(_kv_table([
            ("Affected Asset", finding.get("affected_asset", "")),
            ("Status", finding.get("status", "")),
            ("Compliance Ref.", finding.get("compliance_framework", "")),
        ], styles, label_width=3.5 * cm, value_width=13.4 * cm))
        block.append(Spacer(1, 6))

        block.append(Paragraph("Description", styles["Label"]))
        block.append(Paragraph(finding.get("description", ""), styles["Body"]))

        block.append(Paragraph("Remediation", styles["Label"]))
        block.append(Paragraph(finding.get("remediation", ""), styles["Body"]))

        block.append(Spacer(1, 4))
        rule = Table([[""]], colWidths=[16.9 * cm], rowHeights=[0.4])
        rule.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.6, HexColor(THEME.hairline))]))
        block.append(rule)
        block.append(Spacer(1, 12))

        story.append(KeepTogether(block))

    story.append(PageBreak())


def build_recommendations(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    recs = data["recommendations"]
    story.append(Paragraph("Recommendations", styles["SectionHeading"]))
    story.append(Paragraph(
        "The following remediation actions are prioritized to deliver the "
        "greatest reduction in organizational risk.", styles["Body"]))
    story.append(Spacer(1, 8))

    header = ["Priority", "Recommendation", "Description"]
    table_data = [[Paragraph(h, styles["TableCellHeader"]) for h in header]]
    for rec in sorted(recs, key=lambda r: r.get("priority", 999)):
        table_data.append([
            Paragraph(str(rec.get("priority", "")), styles["TableCell"]),
            Paragraph(str(rec.get("title", "")), styles["TableCell"]),
            Paragraph(str(rec.get("description", "")), styles["TableCell"]),
        ])
    t = Table(table_data, colWidths=[1.8 * cm, 5.0 * cm, 10.1 * cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(THEME.primary)),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor(THEME.hairline)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor(THEME.panel_bg)]),
    ]))
    story.append(t)
    story.append(PageBreak())


def build_compliance_and_appendix(story: List, styles: Dict[str, ParagraphStyle], data: Dict[str, Any]) -> None:
    compliance = data["compliance_mapping"]
    appendix = data["appendix"]
    references = data["references"]

    story.append(Paragraph("Compliance Mapping", styles["SectionHeading"]))
    header = ["Framework", "Control Reference"]
    table_data = [[Paragraph(h, styles["TableCellHeader"]) for h in header]]
    for row in compliance:
        table_data.append([
            Paragraph(str(row.get("framework", "")), styles["TableCell"]),
            Paragraph(str(row.get("control", "")), styles["TableCell"]),
        ])
    t = Table(table_data, colWidths=[8.4 * cm, 8.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor(THEME.primary)),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor(THEME.hairline)),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor(THEME.panel_bg)]),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Appendix", styles["SectionHeading"]))
    story.append(Paragraph("Tools Used", styles["SubHeading"]))
    tools_text = ", ".join(appendix.get("tools", []))
    story.append(Paragraph(tools_text, styles["Body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("References", styles["SubHeading"]))
    for ref in references:
        story.append(Paragraph(f"\u2022 {ref}", styles["Body"]))

    story.append(Spacer(1, 20))
    footer = data["footer"]
    story.append(Paragraph(
        f'{footer.get("copyright", "")} \u2014 {footer.get("confidentiality", "")}',
        styles["BodyMuted"]))


# =====================================================
# PUBLIC ENTRY POINT
# =====================================================

def render_report_pdf(report_data: Dict[str, Any], output_path: str) -> str:
    """Render the full report to a PDF file.

    Args:
        report_data: The dict produced by ReportBuilder.build().
        output_path: Destination .pdf path.

    Returns:
        The output_path, for convenient chaining.
    """
    styles = build_stylesheet()
    report_title = report_data["cover"].get("title", "Security Assessment Report")

    frame_kwargs = dict(
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    content_frame = Frame(
        THEME.margin_side, THEME.margin_bottom,
        THEME.page_size[0] - 2 * THEME.margin_side,
        THEME.page_size[1] - THEME.margin_top - THEME.margin_bottom,
        **frame_kwargs,
    )
    cover_frame = Frame(
        THEME.margin_side, THEME.margin_bottom,
        THEME.page_size[0] - 2 * THEME.margin_side,
        THEME.page_size[1] - THEME.margin_bottom - 1.0 * cm,
        **frame_kwargs,
    )

    doc = ReportDocTemplate(
        output_path,
        pagesize=THEME.page_size,
        title=report_title,
        author="CYART Offensive Security Team",
        subject="Security Assessment Report",
    )
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=_cover_page_background),
        PageTemplate(id="standard", frames=[content_frame],
                      onPage=lambda c, d: _header_footer_content(c, d, report_title)),
    ])

    story: List = []
    build_cover(story, styles, report_data)
    build_document_control(story, styles, report_data)
    build_toc(story, styles)
    build_executive_summary(story, styles, report_data)
    build_scope_and_methodology(story, styles, report_data)
    build_asset_inventory(story, styles, report_data)
    build_risk_matrix(story, styles, report_data)
    build_findings(story, styles, report_data)
    build_recommendations(story, styles, report_data)
    build_compliance_and_appendix(story, styles, report_data)

    logger.info("Rendering PDF report to %s", output_path)
    doc.multiBuild(story, canvasmaker=NumberedCanvas)
    logger.info("PDF report rendered successfully: %s", output_path)
    return output_path

