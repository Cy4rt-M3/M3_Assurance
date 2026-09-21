"""Tests for the CYART-style PDF rendering engine (port of nebula pdf_renderer)."""

from collections.abc import Iterable
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import KeepTogether, Paragraph, Table

from apps.report_generator.pdf_report import (  # type: ignore[reportPrivateUsage]
    THEME,
    _cover_page_background,  # type: ignore[reportPrivateUsage]
    _header_footer_content,  # type: ignore[reportPrivateUsage]
    _kv_table,  # type: ignore[reportPrivateUsage]
    build_asset_inventory,  # type: ignore[reportPrivateUsage]
    build_compliance_and_appendix,  # type: ignore[reportPrivateUsage]
    build_cover,  # type: ignore[reportPrivateUsage]
    build_document_control,  # type: ignore[reportPrivateUsage]
    build_executive_summary,  # type: ignore[reportPrivateUsage]
    build_findings,  # type: ignore[reportPrivateUsage]
    build_recommendations,  # type: ignore[reportPrivateUsage]
    build_risk_matrix,  # type: ignore[reportPrivateUsage]
    build_scope_and_methodology,  # type: ignore[reportPrivateUsage]
    build_stylesheet,  # type: ignore[reportPrivateUsage]
    build_toc,  # type: ignore[reportPrivateUsage]
    cvss_gauge,  # type: ignore[reportPrivateUsage]
    normalize_severity,  # type: ignore[reportPrivateUsage]
    render_report_pdf,  # type: ignore[reportPrivateUsage]
    report_pdf_bytes,  # type: ignore[reportPrivateUsage]
    severity_badge_table,  # type: ignore[reportPrivateUsage]
    severity_color,  # type: ignore[reportPrivateUsage]
    severity_distribution_chart,  # type: ignore[reportPrivateUsage]
)

FROM_NEBULA = datetime(2026, 7, 13, 2, 30, tzinfo=UTC)


def _styles() -> dict[str, ParagraphStyle]:
    return build_stylesheet()


def _data() -> dict[str, Any]:
    return {
        "cover": {
            "report_id": "RPT-0001",
            "title": "CYART Security Assessment Report",
            "generated_at": FROM_NEBULA,
        },
        "organization": {
            "name": "CYART",
            "industry": "Cybersecurity",
            "website": "https://cyart.io",
            "email": "sec@cyart.io",
            "phone": "+91-9876543210",
            "country": "India",
            "city": "Mumbai",
            "address": "Mumbai",
            "contact_person": "Team CYART",
        },
        "scope": {
            "assessment_name": "Internal Security Assessment",
            "assessment_type": "Web App Pentest",
            "target": "CYART Production",
            "assessment_period": "July 2026",
            "assessment_team": "CYART Offensive Team",
            "framework": "NIST CSF",
            "testing_type": "Authenticated",
        },
        "methodology": {
            "Planning": True,
            "Reconnaissance": True,
            "Vulnerability Assessment": True,
            "Manual Validation": True,
            "Risk Analysis": True,
            "Reporting": True,
        },
        "assets": [
            {
                "asset_id": "AST-0001",
                "hostname": "WEB-PROD-01",
                "ip_address": "192.168.1.10",
                "operating_system": "Ubuntu 24.04",
                "asset_type": "Web Server",
                "environment": "Production",
                "criticality": "Critical",
                "owner": "Infra Team",
                "status": "Active",
                "last_scan": FROM_NEBULA,
            },
            {
                "asset_id": "AST-0002",
                "hostname": "DB-PROD-01",
                "ip_address": "192.168.1.20",
                "operating_system": "Ubuntu 22.04",
                "asset_type": "Database Server",
                "environment": "Production",
                "criticality": "High",
                "owner": "DBA Team",
                "status": "Active",
                "last_scan": FROM_NEBULA,
            },
        ],
        "findings": [
            {
                "finding_id": "FND-0001",
                "title": "SQL Injection",
                "description": "SQL Injection in login endpoint allowing DB manipulation.",
                "severity": "Critical",
                "cvss_score": 9.8,
                "affected_asset": "WEB-PROD-01",
                "remediation": "Use parameterized queries.",
                "compliance_framework": "OWASP Top 10",
                "status": "Open",
                "discovered_at": FROM_NEBULA,
            },
            {
                "finding_id": "FND-0002",
                "title": "Outdated Apache",
                "description": "Apache version outdated with known CVEs.",
                "severity": "High",
                "cvss_score": 8.4,
                "affected_asset": "WEB-PROD-01",
                "remediation": "Upgrade Apache to the latest stable release.",
                "compliance_framework": "NIST CSF",
                "status": "Open",
                "discovered_at": FROM_NEBULA,
            },
            {
                "finding_id": "FND-0003",
                "title": "Weak TLS",
                "description": "TLS 1.0 enabled on production server.",
                "severity": "Medium",
                "cvss_score": 5.6,
                "affected_asset": "WEB-PROD-01",
                "remediation": "Disable TLS 1.0 and 1.1.",
                "compliance_framework": "PCI DSS",
                "status": "Open",
                "discovered_at": FROM_NEBULA,
            },
        ],
        "statistics": {
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 0,
            "informational": 0,
            "average_cvss": 8.03,
        },
        "risk_matrix": {"Critical": 1, "High": 1, "Medium": 1, "Low": 0},
        "recommendations": [
            {"priority": 1, "title": "Upgrade Apache", "description": "Upgrade to the latest stable version."},
            {"priority": 2, "title": "Prevent SQL Injection", "description": "Adopt parameterized queries."},
            {"priority": 3, "title": "Disable Weak TLS", "description": "Enforce TLS 1.2+ only."},
        ],
        "appendix": {
            "tools": ["Nmap", "Nessus", "Burp Suite Professional", "OWASP ZAP"],
            "report_version": "1.0",
            "classification": "Confidential",
        },
        "references": ["OWASP Top 10", "NIST Cyber Security Framework", "MITRE ATT&CK", "CIS Controls"],
        "compliance_mapping": [
            {"framework": "NIST CSF", "control": "PR.IP-12"},
            {"framework": "ISO 27001", "control": "A.12.6.1"},
        ],
        "footer": {"company": "CYART", "copyright": "\u00a9 2026 CYART", "confidentiality": "CONFIDENTIAL"},
        "executive_summary": {
            "summary_text": (
                "The assessment identified 1 Critical, 1 High, 1 Medium and 0 Low severity "
                "findings. The average CVSS score is 8.03. The overall organizational risk is "
                "Critical."
            ),
            "overall_risk": "Critical",
        },
        "dashboard": {},
    }


def _empty_data() -> dict[str, Any]:
    return {
        "cover": {"report_id": "RPT-0", "title": "Empty Report", "generated_at": None},
        "organization": {"name": "Org", "contact_person": "", "email": ""},
        "scope": {
            "assessment_name": "",
            "assessment_type": "",
            "target": "",
            "assessment_period": "",
            "assessment_team": "",
            "framework": "",
            "testing_type": "",
        },
        "methodology": {"Phase A": True},
        "assets": [],
        "findings": [],
        "statistics": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0, "average_cvss": 0.0},
        "risk_matrix": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        "recommendations": [],
        "appendix": {"tools": [], "report_version": "1.0", "classification": "Confidential"},
        "references": [],
        "compliance_mapping": [],
        "footer": {"copyright": "", "confidentiality": ""},
        "executive_summary": {"summary_text": "", "overall_risk": "Unknown"},
        "dashboard": {},
    }


def _cell_text(cell: Any) -> list[str]:
    """Flatten a single table cell into its text fragments."""
    if isinstance(cell, Table):
        return _table_texts(cell)
    if isinstance(cell, Paragraph):
        return [cell.text]
    return [str(cell)]


def _table_texts(table: Any) -> list[str]:
    out: list[str] = []
    for row in table._cellvalues:
        for cell in row:
            out.extend(_cell_text(cell))
    return out


def _flowable_texts(flowable: Any) -> list[str]:
    """Flatten one story flowable into its plain-text fragments."""
    if isinstance(flowable, Paragraph):
        return [flowable.text]
    if isinstance(flowable, Table):
        return _table_texts(flowable)
    if isinstance(flowable, KeepTogether):
        return _texts(getattr(flowable, "_content", []))
    return []


def _texts(flowables: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for flowable in flowables:
        out.extend(_flowable_texts(flowable))
    return out


def _joined_texts(flowables: Iterable[Any]) -> str:
    return "\n".join(_texts(flowables))


def test_severity_color_known_and_unknown():
    assert severity_color("Critical") == colors.HexColor(THEME.critical)
    assert severity_color("critical") == colors.HexColor(THEME.critical)
    assert severity_color(" HIGH ") == colors.HexColor(THEME.high)
    assert severity_color("bogus") == colors.HexColor(THEME.muted)
    assert severity_color("") == colors.HexColor(THEME.muted)


def test_normalize_severity():
    assert normalize_severity("Critical") == "critical"
    assert normalize_severity("MEDIUM") == "medium"
    assert normalize_severity("nonsense") == "informational"
    assert normalize_severity("") == "informational"


def test_stylesheet_contains_required_styles():
    styles = _styles()
    for name in [
        "CoverTitle",
        "CoverSubtitle",
        "SectionHeading",
        "SubHeading",
        "Body",
        "BodyMuted",
        "Label",
        "TableCell",
        "TableCellHeader",
        "TOCHeading",
        "ExecSummaryStat",
        "ExecSummaryStatLabel",
    ]:
        assert name in styles
    assert styles["CoverTitle"].textColor == colors.white


def test_charts_and_gauge():
    chart = severity_distribution_chart({"critical": 3, "high": 1})
    assert chart.width == 460
    chart_empty = severity_distribution_chart({})
    assert chart_empty is not None
    assert cvss_gauge(9.4).getContents()
    assert cvss_gauge(7.5) is not None
    assert cvss_gauge(5.6) is not None
    assert cvss_gauge(2.0) is not None
    assert cvss_gauge(0) is not None
    assert cvss_gauge(99) is not None


def test_badge_table_text_and_style():
    badge = severity_badge_table("high")
    assert _table_texts(badge) == ["High"]
    badge_unknown = severity_badge_table("??")
    assert _table_texts(badge_unknown) == ["Informational"]


def test_build_cover_renders_meta():
    story: list[Any] = []
    build_cover(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "CYART Security Assessment Report" in texts
    assert "Web App Pentest" in texts
    assert "Prepared For" in texts
    assert "Report ID" in texts
    assert "RPT-0001" in texts
    assert "13 July 2026" in texts


def test_build_cover_fallback_dates():
    no_date = _data()
    no_date["cover"]["generated_at"] = None
    story: list[Any] = []
    build_cover(story, _styles(), no_date)
    assert _texts(story) is not None

    text_date = _data()
    text_date["cover"]["generated_at"] = "2026-07-13"
    story2: list[Any] = []
    build_cover(story2, _styles(), text_date)
    assert "2026-07-13" in _joined_texts(story2)


def test_build_document_control_fields():
    story: list[Any] = []
    build_document_control(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "Document Control" in texts
    assert "13 Jul 2026" in texts
    assert "M3 Offensive Security Team" in texts
    assert "Initial release" in texts
    assert "Confidential" in texts
    assert "Distribution List" in texts
    assert "CYART" in texts
    assert "Team CYART" in texts


def test_build_document_control_text_dates():
    text_date = _data()
    text_date["cover"]["generated_at"] = "2026-07-13"
    story: list[Any] = []
    build_document_control(story, _styles(), text_date)
    assert "2026-07-13" in _joined_texts(story)


def test_build_toc_heading():
    story: list[Any] = []
    build_toc(story, _styles())
    assert "Table of Contents" in _joined_texts(story)


def test_executive_summary_content():
    story: list[Any] = []
    build_executive_summary(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "Executive Summary" in texts
    assert "OVERALL ORGANIZATIONAL RISK: CRITICAL" in texts
    assert "The average CVSS score is 8.03" in texts
    assert "Findings by Severity" in texts
    assert "TOTAL FINDINGS" in texts
    assert "3" in texts
    assert "AVERAGE CVSS" in texts
    assert "CRITICAL + HIGH" in texts
    assert "2" in texts
    assert "ASSETS IN SCOPE" in texts


def test_scope_and_methodology_content():
    story: list[Any] = []
    build_scope_and_methodology(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "Scope & Methodology" in texts
    assert "Assessment Scope" in texts
    assert "Internal Security Assessment" in texts
    assert "CYART Production" in texts
    assert "July 2026" in texts
    assert "NIST CSF" in texts
    assert "Authenticated" in texts
    assert "1. Planning" in texts
    assert "6. Reporting" in texts


def test_asset_inventory_rows():
    story: list[Any] = []
    build_asset_inventory(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "Asset Inventory" in texts
    assert "2 asset(s) were included within the scope of this assessment." in texts
    assert "WEB-PROD-01" in texts
    assert "DB-PROD-01" in texts
    assert "192.168.1.10" in texts
    assert "Ubuntu 24.04" in texts


def test_risk_matrix_columns_and_values():
    story: list[Any] = []
    build_risk_matrix(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "Risk Matrix" in texts
    for label in ["Critical", "High", "Medium", "Low", "Informational"]:
        assert label in texts
    for value in ["1", "1", "1", "0"]:
        assert value in texts


def test_findings_ordered_by_severity():
    story: list[Any] = []
    build_findings(story, _styles(), _data())
    listed = _texts(story)
    joined = "\n".join(listed)
    assert "Detailed Findings" in joined
    assert "3 finding(s) identified during the" in joined
    sql_idx = listed.index("FND-0001: SQL Injection")
    apache_idx = listed.index("FND-0002: Outdated Apache")
    tls_idx = listed.index("FND-0003: Weak TLS")
    assert sql_idx < apache_idx < tls_idx
    assert "Critical" in joined
    assert "CVSS Score" in joined
    assert "Use parameterized queries." in joined
    assert "Disable TLS 1.0 and 1.1." in joined
    assert "Affected Asset" in joined


def test_findings_empty_case():
    story: list[Any] = []
    build_findings(story, _styles(), _empty_data())
    assert "0 finding(s) identified during the" in _joined_texts(story)


def test_recommendations_sorted_and_fields():
    story: list[Any] = []
    build_recommendations(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "Recommendations" in texts
    assert "Priority" in texts
    assert "Upgrade Apache" in texts
    assert "Prevent SQL Injection" in texts


def test_compliance_appendix_and_footer():
    story: list[Any] = []
    build_compliance_and_appendix(story, _styles(), _data())
    texts = _joined_texts(story)
    assert "Compliance Mapping" in texts
    assert "NIST CSF" in texts
    assert "PR.IP-12" in texts
    assert "A.12.6.1" in texts
    assert "Appendix" in texts
    assert "Tools Used" in texts
    assert "Nmap, Nessus, Burp Suite Professional, OWASP ZAP" in texts
    assert "\u2022 OWASP Top 10" in texts
    assert "\u2022 MITRE ATT&amp;CK" in texts
    assert "\u00a9 2026 CYART \u2014 CONFIDENTIAL" in texts


def test_escape_text_shields_markup():
    from apps.report_generator.pdf_report import (
        _escape_text,  # type: ignore[reportPrivateUsage]
    )

    assert _escape_text("A & B <C>") == "A &amp; B &lt;C&gt;"


def test_kv_table_layout():
    table = _kv_table([("Label A", "Value A"), ("Label B", "Value B")], _styles())
    assert _table_texts(table) == ["Label A", "Value A", "Label B", "Value B"]


def test_header_footer_draw_callback():
    buffer = BytesIO()
    canvas_obj = pdfcanvas.Canvas(buffer, pagesize=THEME.page_size)
    _header_footer_content(canvas_obj, None, "CYART Security Assessment Report")  # type: ignore[arg-type]
    assert getattr(canvas_obj, "_is_cover_page") is False  # noqa: B009


def test_cover_background_draw_callback():
    buffer = BytesIO()
    canvas_obj = pdfcanvas.Canvas(buffer, pagesize=THEME.page_size)
    _cover_page_background(canvas_obj, None)  # type: ignore[arg-type]
    assert getattr(canvas_obj, "_is_cover_page") is True  # noqa: B009


def test_report_pdf_bytes_output():
    pdf = report_pdf_bytes(_data())
    assert pdf.startswith(b"%PDF-")


def test_render_report_pdf_to_file(tmp_path: Path) -> None:
    output = render_report_pdf(_data(), str(tmp_path / "report.pdf"))
    rendered = (tmp_path / "report.pdf").read_bytes()
    assert output == str(tmp_path / "report.pdf")
    assert rendered.startswith(b"%PDF-")


def test_render_empty_data_no_crash():
    pdf = report_pdf_bytes(_empty_data())
    assert pdf.startswith(b"%PDF-")
    assert b"/Type /Page" in pdf


def test_numbered_canvas_page_total_annotations():
    pdf = report_pdf_bytes(_data())
    assert b"Page " not in pdf or b"/Count" in pdf