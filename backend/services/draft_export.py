"""
Document Exporters for Legal Drafts (PDF & DOCX)
Generates court-styled, formatted PDF and DOCX documents with legal headers,
proper typographic hierarchy, pagination, legal disclaimers, and citation appendices.
"""

import io
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.pdfgen import canvas

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from schemas.drafts import ExportDraftRequest, DraftSection, CitationInfo


# ── Numbered Canvas for "Page X of Y" in ReportLab ───────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))

        # Running header (pages 2+)
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(40, 805, 555, 805)
            self.drawString(40, 810, "NYAYASARATHI — LEGAL DRAFTING & RESEARCH PLATFORM")
            self.drawRightString(555, 810, "PRELIMINARY DRAFT — FOR ADVOCATE REVIEW ONLY")

        # Running footer (all pages)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(40, 42, 555, 42)
        self.drawString(40, 30, "Generated via NyayaSarathi AI • Confidential & Privileged")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(555, 30, page_text)
        self.restoreState()


# ── PDF Generation ────────────────────────────────────────────────────────────
def generate_draft_pdf(request: ExportDraftRequest) -> bytes:
    """
    Generates a high-quality, court-styled legal PDF document from a draft.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=48,
        bottomMargin=54,
    )

    base_styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "LegalTitle",
        parent=base_styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=1,  # Center
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=10,
    )

    doc_type_style = ParagraphStyle(
        "DocTypeStyle",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=1,  # Center
        textColor=colors.HexColor("#6E2634"),  # Oxblood
        spaceAfter=14,
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10.5,
        alignment=4,  # Justified
        textColor=colors.HexColor("#4A4A4A"),
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1D211F"),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "LegalBody",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        alignment=4,  # Justified
        textColor=colors.HexColor("#1F1F1F"),
        spaceAfter=7,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#222222"),
    )

    story = []

    # Title & Sub-header
    story.append(Paragraph(request.title.upper(), title_style))
    story.append(Paragraph(f"[ {request.document_type.replace('_', ' ').upper()} ]", doc_type_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#B59A68"), spaceAfter=10))

    # Legal Disclaimer Banner Box
    disclaimer_text = (
        "<b>LEGAL DISCLAIMER & NOTICE OF REVIEW:</b> This document is an initial structured draft "
        "generated by the NyayaSarathi Legal Intelligence Platform for professional legal assistance. "
        "It does not constitute formal legal advice, certification, or court-ready pleadings. "
        "Every factual averment, jurisdiction clause, and statutory ground must be verified and approved "
        "by an advocate admitted to practice in the competent jurisdiction prior to execution or filing."
    )
    disclaimer_p = Paragraph(disclaimer_text, disclaimer_style)
    disclaimer_table = Table(
        [[disclaimer_p]],
        colWidths=[511],
    )
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F5F0")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#B59A68")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 14))

    # Sections
    sorted_sections = sorted(request.sections, key=lambda s: s.order)
    for idx, sec in enumerate(sorted_sections, start=1):
        if len(sorted_sections) > 1 and sec.id != "final_draft":
            heading_text = f"{idx}. {sec.title.upper()}"
            story.append(Paragraph(heading_text, section_heading_style))

        # Split content into paragraphs
        paras = [p.strip() for p in sec.content.split("\n\n") if p.strip()]
        if not paras:
            paras = [sec.content.strip()]

        for p_text in paras:
            # Clean up line breaks within paragraphs
            clean_p = p_text.replace("\n", "<br/>")
            # Highlight missing info tags in red italic
            clean_p = re.sub(
                r"(\[MISSING:[^\]]+\])",
                r'<font color="#8A3545"><b>\1</b></font>',
                clean_p
            )
            story.append(Paragraph(clean_p, body_style))

        story.append(Spacer(1, 6))



    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


# ── DOCX Generation ───────────────────────────────────────────────────────────
def generate_draft_docx(request: ExportDraftRequest) -> bytes:
    """
    Generates a clean, editable DOCX Word document with standard legal styling.
    """
    doc = docx.Document()

    # Page setup: A4 with 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)

    # Base styling
    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Georgia"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(6)

    # Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(request.title.upper())
    title_run.font.name = "Georgia"
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)

    # Subtitle / Document Type
    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run(f"[ {request.document_type.replace('_', ' ').upper()} ]\n")
    sub_run.font.name = "Georgia"
    sub_run.font.size = Pt(11)
    sub_run.font.bold = True
    sub_run.font.color.rgb = RGBColor(0x6E, 0x26, 0x34)  # Oxblood

    # Legal Disclaimer callout
    disc_table = doc.add_table(rows=1, cols=1)
    disc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    disc_cell = disc_table.cell(0, 0)
    disc_cell.width = Inches(6.27)

    # Shading XML
    shading_elm = parse_xml(r'<w:shd {} w:fill="F7F5F0"/>'.format(nsdecls('w')))
    disc_cell._tc.get_or_add_tcPr().append(shading_elm)

    dp = disc_cell.paragraphs[0]
    dp.paragraph_format.space_before = Pt(4)
    dp.paragraph_format.space_after = Pt(4)
    dp.paragraph_format.left_indent = Inches(0.1)
    dp.paragraph_format.right_indent = Inches(0.1)

    d_bold = dp.add_run("LEGAL DISCLAIMER & NOTICE OF REVIEW: ")
    d_bold.font.size = Pt(8.5)
    d_bold.font.bold = True
    d_bold.font.color.rgb = RGBColor(0x8A, 0x35, 0x45)

    d_text = dp.add_run(
        "This document is an initial structured draft generated by the NyayaSarathi Legal Intelligence "
        "Platform for advocate assistance. It does not constitute formal legal certification or certified pleadings. "
        "Review by an admitted advocate is required before execution or filing."
    )
    d_text.font.size = Pt(8.5)
    d_text.font.italic = True
    d_text.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_paragraph()  # Spacer

    # Sections
    sorted_sections = sorted(request.sections, key=lambda s: s.order)
    for idx, sec in enumerate(sorted_sections, start=1):
        if len(sorted_sections) > 1 and sec.id != "final_draft":
            # Section Heading
            hp = doc.add_paragraph()
            hp.paragraph_format.space_before = Pt(12)
            hp.paragraph_format.space_after = Pt(4)
            hp.paragraph_format.keep_with_next = True
            hrun = hp.add_run(f"{idx}. {sec.title.upper()}")
            hrun.font.name = "Georgia"
            hrun.font.size = Pt(12)
            hrun.font.bold = True
            hrun.font.color.rgb = RGBColor(0x1D, 0x21, 0x1F)

        # Content paragraphs
        paras = [p.strip() for p in sec.content.split("\n\n") if p.strip()]
        if not paras:
            paras = [sec.content.strip()]

        for p_text in paras:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            # Handle missing information highlighting
            parts = re.split(r"(\[MISSING:[^\]]+\])", p_text)
            for part in parts:
                if re.match(r"\[MISSING:[^\]]+\]", part):
                    r = p.add_run(part)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0x8A, 0x35, 0x45)
                else:
                    p.add_run(part)



    # Footer on all sections
    for s in doc.sections:
        footer = s.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun = fp.add_run("NyayaSarathi AI Legal Drafting • Confidential")
        frun.font.size = Pt(8)
        frun.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
