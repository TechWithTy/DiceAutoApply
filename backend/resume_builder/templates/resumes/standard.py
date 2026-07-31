import json
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    HRFlowable,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors


# -----------------------------
# Template + Layout Controls
# -----------------------------
@dataclass
class ResumeTheme:
    page_size: tuple = letter
    left_margin: float = 0.6 * inch
    right_margin: float = 0.6 * inch
    top_margin: float = 0.6 * inch
    bottom_margin: float = 0.6 * inch

    accent_color: str = "#0C6398"

    # Typography
    name_font_size: int = 16
    headline_font_size: float = 9.8
    body_font_size: float = 9.5
    body_leading: float = 12.0
    section_font_size: int = 11

    # Spacing
    header_gap: float = 8
    section_space_before: float = 8
    section_space_after: float = 4
    paragraph_space_after: float = 2
    role_gap: float = 6
    bullet_indent: int = 12
    bullet_left_pad: int = 8


def build_styles(theme: ResumeTheme):
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=theme.name_font_size,
        spaceAfter=4,
        textColor=colors.black,
    )

    headline_style = ParagraphStyle(
        "HeadlineStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=theme.headline_font_size,
        leading=theme.body_leading,
        spaceAfter=2,
        textColor=colors.black,
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=theme.section_font_size,
        textColor=colors.HexColor(theme.accent_color),
        spaceBefore=theme.section_space_before,
        spaceAfter=theme.section_space_after,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=theme.body_font_size,
        leading=theme.body_leading,
        spaceAfter=theme.paragraph_space_after,
        textColor=colors.black,
    )

    body_style_small = ParagraphStyle(
        "BodyStyleSmall",
        parent=body_style,
        fontSize=theme.body_font_size - 0.2,
    )

    return {
        "header": header_style,
        "headline": headline_style,
        "section": section_style,
        "body": body_style,
        "body_small": body_style_small,
    }


# -----------------------------
# Helpers
# -----------------------------
def p(text: str) -> str:
    """Basic HTML-safe-ish paragraph string. Keep it minimal; ReportLab supports <b>, <br/>."""
    return text.replace("\n", "<br/>")


def add_section_header(elements, styles, title: str, theme: ResumeTheme):
    elements.append(Paragraph(title, styles["section"]))
    # Subtle divider line (ATS-safe)
    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.6,
            color=colors.lightgrey,
            spaceBefore=1,
            spaceAfter=6,
            lineCap="round",
        )
    )


def add_bullets(elements, styles, bullets: List[str], theme: ResumeTheme):
    items = []
    for b in bullets:
        items.append(ListItem(Paragraph(p(b), styles["body"]), leftIndent=theme.bullet_indent))
    elements.append(
        ListFlowable(
            items,
            bulletType="bullet",
            leftPadding=theme.bullet_left_pad,
            bulletFontName="Helvetica",
            bulletFontSize=theme.body_font_size,
        )
    )


# -----------------------------
# Main Builder
# -----------------------------
def build_resume(data: Dict[str, Any], out_path: str, theme: Optional[ResumeTheme] = None):
    theme = theme or ResumeTheme()
    styles = build_styles(theme)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=theme.page_size,
        leftMargin=theme.left_margin,
        rightMargin=theme.right_margin,
        topMargin=theme.top_margin,
        bottomMargin=theme.bottom_margin,
        title=f"{data.get('name','Resume')}",
        author=data.get("name", ""),
    )

    elements = []

    # Header
    elements.append(Paragraph(data["name"].upper(), styles["header"]))
    if data.get("headline"):
        elements.append(Paragraph(p(data["headline"]), styles["headline"]))

    contact_parts = data.get("contact", [])
    if contact_parts:
        elements.append(Paragraph(" • ".join(contact_parts), styles["body_small"]))

    if data.get("links_line"):
        # optional single line like: "Portfolio: ... | GitHub: ..."
        elements.append(Paragraph(p(data["links_line"]), styles["body_small"]))

    elements.append(Spacer(1, theme.header_gap))

    # Summary
    if data.get("summary"):
        add_section_header(elements, styles, "PROFESSIONAL SUMMARY", theme)
        elements.append(Paragraph(p(data["summary"]), styles["body"]))

    # Skills (supports either list of categories or a single HTML string)
    if data.get("skills"):
        add_section_header(elements, styles, "CORE TECHNICAL SKILLS", theme)
        skills = data["skills"]
        if isinstance(skills, str):
            elements.append(Paragraph(p(skills), styles["body"]))
        else:
            # list of {"label": "...", "items": ["...", "..."]} or {"label":"", "text": "..."}
            lines = []
            for s in skills:
                label = s.get("label", "").strip()
                if "text" in s:
                    val = s["text"]
                else:
                    val = ", ".join(s.get("items", []))
                if label:
                    lines.append(f"<b>{label}:</b> {val}")
                else:
                    lines.append(val)
            elements.append(Paragraph("<br/>".join(lines), styles["body"]))

    # Experience
    if data.get("experience"):
        add_section_header(elements, styles, "PROFESSIONAL EXPERIENCE", theme)
        for role in data["experience"]:
            title = role.get("title", "")
            org = role.get("org", "")
            dates = role.get("dates", "")
            location = role.get("location", "")

            header_line = f"<b>{org}</b> — {title}"
            if dates:
                header_line += f" | {dates}"
            elements.append(Spacer(1, theme.role_gap))
            elements.append(Paragraph(p(header_line), styles["body"]))
            if location:
                elements.append(Paragraph(f"<font color='#334155'>{p(location)}</font>", styles["body_small"]))

            bullets = role.get("bullets", [])
            if bullets:
                add_bullets(elements, styles, bullets, theme)

    # Projects
    if data.get("projects"):
        add_section_header(elements, styles, "SELECTED PROJECTS", theme)
        for pr in data["projects"]:
            elements.append(Spacer(1, 4))
            line = f"<b>{pr.get('name','')}</b>"
            if pr.get("stack"):
                line += f" — {pr['stack']}"
            elements.append(Paragraph(p(line), styles["body"]))
            if pr.get("bullets"):
                add_bullets(elements, styles, pr["bullets"], theme)

    # Education
    if data.get("education"):
        add_section_header(elements, styles, "EDUCATION", theme)
        # education can be list or string
        edu = data["education"]
        if isinstance(edu, str):
            elements.append(Paragraph(p(edu), styles["body"]))
        else:
            for e in edu:
                line = e.get("school", "")
                if e.get("degree"):
                    line += f" — {e['degree']}"
                if e.get("dates"):
                    line += f" ({e['dates']})"
                elements.append(Paragraph(p(line), styles["body"]))

    # Certifications (optional)
    if data.get("certifications"):
        add_section_header(elements, styles, "CERTIFICATIONS", theme)
        certs = data["certifications"]
        if isinstance(certs, str):
            elements.append(Paragraph(p(certs), styles["body"]))
        else:
            add_bullets(elements, styles, certs, theme)

    doc.build(elements)
