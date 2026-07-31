import json
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors


# -----------------------------
# Template + Layout Controls
# -----------------------------
@dataclass
class CoverLetterTheme:
    page_size: tuple = letter
    left_margin: float = 1.0 * inch
    right_margin: float = 1.0 * inch
    top_margin: float = 1.0 * inch
    bottom_margin: float = 1.0 * inch

    # Typography
    name_font_size: int = 16
    headline_font_size: float = 10
    body_font_size: float = 11
    body_leading: float = 15.0

    # Spacing
    header_gap: float = 24
    paragraph_space_after: float = 12


def build_styles(theme: CoverLetterTheme):
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
        leading=14.0,
        spaceAfter=2,
        textColor=colors.black,
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
        fontSize=theme.headline_font_size,
        spaceAfter=2,
    )

    return {
        "header": header_style,
        "headline": headline_style,
        "body": body_style,
        "body_small": body_style_small,
    }


# -----------------------------
# Helpers
# -----------------------------
def p(text: str) -> str:
    """Basic HTML-safe-ish paragraph string."""
    return text.replace("\n", "<br/>")


# -----------------------------
# Main Builder
# -----------------------------
def build_cover_letter(data: Dict[str, Any], out_path: str, theme: Optional[CoverLetterTheme] = None):
    theme = theme or CoverLetterTheme()
    styles = build_styles(theme)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=theme.page_size,
        leftMargin=theme.left_margin,
        rightMargin=theme.right_margin,
        topMargin=theme.top_margin,
        bottomMargin=theme.bottom_margin,
        title=f"Cover Letter - {data.get('name','Applicant')}",
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
        elements.append(Paragraph(p(data["links_line"]), styles["body_small"]))

    elements.append(Spacer(1, theme.header_gap))

    # Date
    if data.get("date"):
        elements.append(Paragraph(p(data["date"]), styles["body"]))
        
    # Recipient Info
    recipient = data.get("recipient", {})
    if recipient:
        recipient_lines = []
        if recipient.get("name"):
            recipient_lines.append(recipient["name"])
        if recipient.get("title"):
            recipient_lines.append(recipient["title"])
        if recipient.get("company"):
            recipient_lines.append(recipient["company"])
        if recipient.get("address"):
            recipient_lines.append(recipient["address"])
        
        if recipient_lines:
            elements.append(Paragraph(p("\n".join(recipient_lines)), styles["body"]))

    # Greeting
    if data.get("greeting"):
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(p(data["greeting"]), styles["body"]))

    # Body Paragraphs
    paragraphs = data.get("paragraphs", [])
    for para in paragraphs:
        elements.append(Paragraph(p(para), styles["body"]))

    # Sign-off
    elements.append(Spacer(1, 12))
    sign_off = data.get("sign_off", "Sincerely,")
    elements.append(Paragraph(p(sign_off), styles["body"]))
    
    # Signature
    signature = data.get("signature", data.get("name", ""))
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(p(signature), styles["body"]))

    doc.build(elements)
