"""
Document Exporters for Legal Drafts (PDF & DOCX)
Generates court-styled, formatted PDF and DOCX documents with legal headers,
proper typographic hierarchy, pagination, legal disclaimers, and citation appendices.
Full native support for Indic scripts (Hindi, Marathi), Rupee sign ₹, Section sign §, and Unicode characters.
"""

import os
import io
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from schemas.drafts import ExportDraftRequest, DraftSection, CitationInfo


# ── TrueType Unicode / Indic Font Registration ────────────────────────────────
_REGISTERED_FONT: Optional[str] = None
_REGISTERED_FONT_BOLD: Optional[str] = None


def get_pdf_fonts() -> Tuple[str, str]:
    """
    Finds and registers a TrueType font supporting Unicode / Devanagari / Indian characters.
    Returns (font_regular, font_bold).
    """
    global _REGISTERED_FONT, _REGISTERED_FONT_BOLD
    if _REGISTERED_FONT and _REGISTERED_FONT_BOLD:
        return _REGISTERED_FONT, _REGISTERED_FONT_BOLD

    candidates = [
        # Windows Nirmala UI (TTC index 0 for Regular, index 1 for Bold)
        ("NirmalaUI", "C:/Windows/Fonts/Nirmala.ttc", 0, "NirmalaUI-Bold", "C:/Windows/Fonts/Nirmala.ttc", 1),
        ("Mangal", "C:/Windows/Fonts/mangal.ttf", None, "Mangal-Bold", "C:/Windows/Fonts/mangalb.ttf", None),
        ("Aparajita", "C:/Windows/Fonts/aparaj.ttf", None, "Aparajita-Bold", "C:/Windows/Fonts/aparajb.ttf", None),
        ("SegoeUI", "C:/Windows/Fonts/segoeui.ttf", None, "SegoeUI-Bold", "C:/Windows/Fonts/segoeuib.ttf", None),
        ("Arial", "C:/Windows/Fonts/arial.ttf", None, "Arial-Bold", "C:/Windows/Fonts/arialbd.ttf", None),
        # Linux / Unix
        ("NotoSansDevanagari", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf", None, "NotoSansDevanagari-Bold", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf", None),
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", None, "DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", None),
    ]

    for reg_name, reg_path, reg_idx, bold_name, bold_path, bold_idx in candidates:
        if os.path.exists(reg_path):
            try:
                if reg_idx is not None:
                    pdfmetrics.registerFont(TTFont(reg_name, reg_path, subfontIndex=reg_idx))
                else:
                    pdfmetrics.registerFont(TTFont(reg_name, reg_path))

                if bold_path and os.path.exists(bold_path):
                    if bold_idx is not None:
                        pdfmetrics.registerFont(TTFont(bold_name, bold_path, subfontIndex=bold_idx))
                    else:
                        pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                else:
                    bold_name = reg_name

                pdfmetrics.registerFontFamily(
                    reg_name,
                    normal=reg_name,
                    bold=bold_name,
                    italic=reg_name,
                    boldItalic=bold_name
                )
                _REGISTERED_FONT = reg_name
                _REGISTERED_FONT_BOLD = bold_name
                return _REGISTERED_FONT, _REGISTERED_FONT_BOLD
            except Exception:
                continue

    _REGISTERED_FONT = "Helvetica"
    _REGISTERED_FONT_BOLD = "Helvetica-Bold"
    return _REGISTERED_FONT, _REGISTERED_FONT_BOLD


def _escape_reportlab_text(text: str) -> str:
    """Escapes XML entities in raw text while preserving intentional inline tags."""
    if not text:
        return ""
    # Escape ampersands not already part of an entity
    escaped = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;)", "&amp;", text)
    # Replace line breaks with ReportLab break
    escaped = escaped.replace("\n", "<br/>")
    return escaped


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
        font_reg, _ = get_pdf_fonts()
        self.setFont(font_reg, 8)
        self.setFillColor(colors.HexColor("#666666"))

        # Running header (pages 2+)
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(40, 805, 555, 805)
            self.drawString(40, 810, "NYAYASARATHI — LEGAL DRAFTING PLATFORM")
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
    Supports native Indic scripts and clean typography.
    """
    font_reg, font_bold = get_pdf_fonts()

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

    title_style = ParagraphStyle(
        "LegalTitle",
        parent=base_styles["Title"],
        fontName=font_bold,
        fontSize=13,
        leading=17,
        alignment=1,  # Center
        textColor=colors.HexColor("#1A1A1A"),
        spaceAfter=8,
    )

    doc_type_style = ParagraphStyle(
        "DocTypeStyle",
        parent=base_styles["Normal"],
        fontName=font_bold,
        fontSize=10,
        leading=13,
        alignment=1,  # Center
        textColor=colors.HexColor("#6E2634"),  # Oxblood
        spaceAfter=12,
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=base_styles["Normal"],
        fontName=font_reg,
        fontSize=7.5,
        leading=11,
        alignment=4,  # Justified
        textColor=colors.HexColor("#4A4A4A"),
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=base_styles["Heading2"],
        fontName=font_bold,
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
        fontName=font_reg,
        fontSize=9.5,
        leading=14.5,
        alignment=4,  # Justified
        textColor=colors.HexColor("#1F1F1F"),
        spaceAfter=7,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=base_styles["Normal"],
        fontName=font_bold,
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=base_styles["Normal"],
        fontName=font_reg,
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#222222"),
    )

    story = []

    # Title & Sub-header
    clean_title = _escape_reportlab_text(request.title.upper())
    story.append(Paragraph(clean_title, title_style))
    doc_type_display = request.document_type.replace("_", " ").upper()
    story.append(Paragraph(f"[ {doc_type_display} ]", doc_type_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#B59A68"), spaceAfter=10))

    # Legal Disclaimer Banner Box
    disclaimer_text = (
        "<b>LEGAL DISCLAIMER & NOTICE OF ADVOCATE REVIEW:</b> This document is an initial structured draft "
        "synthesized by the NyayaSarathi Legal Intelligence Platform for professional advocate assistance. "
        "It does not constitute formal legal certification or certified pleadings. "
        "Every factual averment, jurisdiction clause, and statutory ground must be verified and approved "
        "by an advocate admitted to practice in the competent jurisdiction prior to execution or court filing."
    )
    disclaimer_p = Paragraph(disclaimer_text, disclaimer_style)
    disclaimer_table = Table([[disclaimer_p]], colWidths=[511])
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

    # Ordered Sections
    sorted_sections = sorted(request.sections, key=lambda s: s.order)
    for idx, sec in enumerate(sorted_sections, start=1):
        if len(sorted_sections) > 1 and sec.id != "final_draft":
            clean_sec_title = _escape_reportlab_text(sec.title.upper())
            heading_text = f"{idx}. {clean_sec_title}"
            story.append(Paragraph(heading_text, section_heading_style))

        paras = [p.strip() for p in sec.content.split("\n\n") if p.strip()]
        if not paras:
            paras = [sec.content.strip()]

        for p_text in paras:
            clean_p = _escape_reportlab_text(p_text)
            # Highlight missing info tags in red bold
            clean_p = re.sub(
                r"(\[(?:MISSING|INFORMATION REQUIRED):[^\]]+\])",
                r'<font color="#8A3545"><b>\1</b></font>',
                clean_p
            )
            story.append(Paragraph(clean_p, body_style))

        story.append(Spacer(1, 6))

    # Citations Appendix (if present)
    if request.citations and len(request.citations) > 0:
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#B59A68"), spaceAfter=8))
        story.append(Paragraph("SCHEDULE / APPENDIX: STATUTORY PROVISIONS & CITATIONS", section_heading_style))
        cit_note = (
            "<i>Note: Citations and statutory references are generated for advocate reference and require "
            "independent verification against primary legal sources prior to court submission.</i>"
        )
        story.append(Paragraph(cit_note, disclaimer_style))
        story.append(Spacer(1, 6))

        table_data = [
            [
                Paragraph("<b>No.</b>", table_header_style),
                Paragraph("<b>Authority / Act</b>", table_header_style),
                Paragraph("<b>Citation / Section</b>", table_header_style),
                Paragraph("<b>Status / Verification</b>", table_header_style),
            ]
        ]
        for c_idx, cit in enumerate(request.citations, start=1):
            status_text = "Verified Primary Source" if cit.is_verified else "Verification Required"
            table_data.append([
                Paragraph(str(c_idx), table_cell_style),
                Paragraph(_escape_reportlab_text(cit.title), table_cell_style),
                Paragraph(_escape_reportlab_text(cit.citation), table_cell_style),
                Paragraph(status_text, table_cell_style),
            ])

        cit_table = Table(table_data, colWidths=[30, 200, 160, 121])
        cit_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6E2634")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(cit_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


# ── DOCX Helper: Set Run Font for Complex Scripts ─────────────────────────────
def _clean_docx_xml_text(text: str) -> str:
    """Removes XML-illegal control characters that corrupt DOCX files."""
    if not text:
        return ""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def _set_run_font(run, font_name: str = "Nirmala UI", size_pt: float = 11, bold: bool = False, italic: bool = False, color_rgb: Optional[RGBColor] = None):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color_rgb:
        run.font.color.rgb = color_rgb

    # Explicitly configure Word complex script font elements
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:cs'), font_name)
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)


# ── DOCX Generation ───────────────────────────────────────────────────────────
def generate_draft_docx(request: ExportDraftRequest) -> bytes:
    """
    Generates a clean, editable DOCX Word document with standard legal styling.
    Configures complex scripts so Devanagari (Hindi/Marathi) and Unicode characters render correctly.
    """
    doc = docx.Document()
    main_font = "Nirmala UI"

    # Page setup: A4 with 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)

    # Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(_clean_docx_xml_text(request.title.upper()))
    _set_run_font(title_run, font_name=main_font, size_pt=15, bold=True, color_rgb=RGBColor(0x1A, 0x1A, 0x1A))

    # Subtitle / Document Type
    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc_type_disp = request.document_type.replace("_", " ").upper()
    sub_run = sub_p.add_run(f"[ {doc_type_disp} ]\n")
    _set_run_font(sub_run, font_name=main_font, size_pt=10.5, bold=True, color_rgb=RGBColor(0x6E, 0x26, 0x34))

    # Legal Disclaimer callout box
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
    _set_run_font(d_bold, font_name=main_font, size_pt=8.5, bold=True, color_rgb=RGBColor(0x8A, 0x35, 0x45))

    d_text = dp.add_run(
        "This document is an initial structured draft synthesized by the NyayaSarathi Legal Intelligence "
        "Platform for advocate assistance. It does not constitute formal legal certification or certified pleadings. "
        "Review and verification by an admitted advocate is required before execution or court filing."
    )
    _set_run_font(d_text, font_name=main_font, size_pt=8.5, italic=True, color_rgb=RGBColor(0x55, 0x55, 0x55))

    doc.add_paragraph()  # Spacer

    # Ordered Sections
    sorted_sections = sorted(request.sections, key=lambda s: s.order)
    for idx, sec in enumerate(sorted_sections, start=1):
        if len(sorted_sections) > 1 and sec.id != "final_draft":
            hp = doc.add_paragraph()
            hp.paragraph_format.space_before = Pt(12)
            hp.paragraph_format.space_after = Pt(4)
            hp.paragraph_format.keep_with_next = True
            hrun = hp.add_run(f"{idx}. {_clean_docx_xml_text(sec.title.upper())}")
            _set_run_font(hrun, font_name=main_font, size_pt=12, bold=True, color_rgb=RGBColor(0x1D, 0x21, 0x1F))

        paras = [p.strip() for p in sec.content.split("\n\n") if p.strip()]
        if not paras:
            paras = [sec.content.strip()]

        for p_text in paras:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(6)

            # Highlight missing information tags
            parts = re.split(r"(\[(?:MISSING|INFORMATION REQUIRED):[^\]]+\])", p_text)
            for part in parts:
                clean_part = _clean_docx_xml_text(part)
                if re.match(r"^\[(?:MISSING|INFORMATION REQUIRED):[^\]]+\]$", part):
                    r = p.add_run(clean_part)
                    _set_run_font(r, font_name=main_font, size_pt=10.5, bold=True, color_rgb=RGBColor(0x8A, 0x35, 0x45))
                else:
                    r = p.add_run(clean_part)
                    _set_run_font(r, font_name=main_font, size_pt=10.5, color_rgb=RGBColor(0x22, 0x22, 0x22))

    # Citations Table in DOCX (if present)
    if request.citations and len(request.citations) > 0:
        ch = doc.add_paragraph()
        ch.paragraph_format.space_before = Pt(16)
        ch.paragraph_format.space_after = Pt(4)
        c_head_run = ch.add_run("SCHEDULE: STATUTORY PROVISIONS & CITATIONS")
        _set_run_font(c_head_run, font_name=main_font, size_pt=12, bold=True, color_rgb=RGBColor(0x1D, 0x21, 0x1F))

        cp = doc.add_paragraph()
        cp_run = cp.add_run("Advocate verification required prior to formal reliance in court pleadings.")
        _set_run_font(cp_run, font_name=main_font, size_pt=8.5, italic=True, color_rgb=RGBColor(0x66, 0x66, 0x66))

        c_table = doc.add_table(rows=1, cols=4)
        c_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = c_table.rows[0].cells
        headers = ["No.", "Authority / Act", "Citation / Section", "Status"]
        for i, h_text in enumerate(headers):
            r = hdr_cells[i].paragraphs[0].add_run(h_text)
            _set_run_font(r, font_name=main_font, size_pt=9, bold=True, color_rgb=RGBColor(0x11, 0x11, 0x11))

        for c_idx, cit in enumerate(request.citations, start=1):
            row_cells = c_table.add_row().cells
            row_cells[0].paragraphs[0].add_run(str(c_idx))
            row_cells[1].paragraphs[0].add_run(_clean_docx_xml_text(cit.title))
            row_cells[2].paragraphs[0].add_run(_clean_docx_xml_text(cit.citation))
            stat = "Verified Primary Source" if cit.is_verified else "Verification Required"
            row_cells[3].paragraphs[0].add_run(stat)
            for cell in row_cells:
                for p in cell.paragraphs:
                    for run in p.runs:
                        _set_run_font(run, font_name=main_font, size_pt=8.5, color_rgb=RGBColor(0x33, 0x33, 0x33))

    # Footer on all sections
    for s in doc.sections:
        footer = s.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun = fp.add_run("NyayaSarathi AI Legal Drafting • Confidential & Privileged")
        _set_run_font(frun, font_name=main_font, size_pt=8, color_rgb=RGBColor(0x88, 0x88, 0x88))

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
