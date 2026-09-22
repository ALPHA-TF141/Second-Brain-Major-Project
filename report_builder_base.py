"""
Generate the complete development report for SecondBrain.
===========================================================================
A full account of how the system was built: the original idea, every phase,
every deviation, the reasoning behind decisions, the user's inputs, the defects
found and their root causes, the concepts and theory involved, and the research
results. Written to be readable by a student, a supervisor, or an examiner.

Usage:  python generate_development_report.py
Output: SECOND_BRAIN_DEVELOPMENT_REPORT.pdf
"""
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

OUT = "SECOND_BRAIN_DEVELOPMENT_REPORT.pdf"
PAGE_W, PAGE_H = A4
MARGIN_X = 62
MARGIN_TOP = 62
MARGIN_BOTTOM = 60
BODY_W = PAGE_W - 2 * MARGIN_X

ACCENT = colors.HexColor("#123a63")
ACCENT2 = colors.HexColor("#7a4a00")
GREY = colors.HexColor("#5a5a5a")
LIGHT = colors.HexColor("#f2f4f7")
RULE = colors.HexColor("#b9c2cc")


def styles():
    def S(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9.6, leading=13.4, alignment=TA_JUSTIFY,
                    spaceAfter=5, textColor=colors.HexColor("#141414"))
        base.update(kw)
        return ParagraphStyle(name, **base)

    return {
        "title": S("title", fontName="Helvetica-Bold", fontSize=27, leading=31,
                   alignment=TA_CENTER, textColor=ACCENT, spaceAfter=10),
        "subtitle": S("subtitle", fontName="Helvetica", fontSize=13.5, leading=18,
                      alignment=TA_CENTER, textColor=GREY, spaceAfter=6),
        "docmeta": S("docmeta", fontName="Courier", fontSize=9, leading=13,
                     alignment=TA_CENTER, textColor=GREY),
        "h1": S("h1", fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=TA_LEFT,
                textColor=ACCENT, spaceBefore=14, spaceAfter=7),
        "h2": S("h2", fontName="Helvetica-Bold", fontSize=12, leading=15.5, alignment=TA_LEFT,
                textColor=colors.HexColor("#1f2d3d"), spaceBefore=11, spaceAfter=5),
        "h3": S("h3", fontName="Helvetica-BoldOblique", fontSize=10.4, leading=13.6,
                alignment=TA_LEFT, textColor=ACCENT2, spaceBefore=8, spaceAfter=4),
        "body": S("body"),
        "bullet": S("bullet", leftIndent=14, bulletIndent=3, spaceAfter=3.4),
        "code": S("code", fontName="Courier", fontSize=8.1, leading=10.4, alignment=TA_LEFT,
                  textColor=colors.HexColor("#10243a"), spaceAfter=0),
        "caption": S("caption", fontName="Helvetica-Oblique", fontSize=8.4, leading=11,
                     alignment=TA_CENTER, textColor=GREY, spaceBefore=3, spaceAfter=9),
        "quote": S("quote", fontName="Helvetica-Oblique", fontSize=9.4, leading=13,
                   leftIndent=16, rightIndent=10, textColor=colors.HexColor("#333333"),
                   spaceBefore=3, spaceAfter=6),
        "tabh": S("tabh", fontName="Helvetica-Bold", fontSize=8.4, leading=10.6,
                  alignment=TA_LEFT),
        "tabc": S("tabc", fontName="Helvetica", fontSize=8.4, leading=10.6, alignment=TA_LEFT),
        "toc1": S("toc1", fontName="Helvetica-Bold", fontSize=9.8, leading=14, spaceAfter=1),
        "toc2": S("toc2", fontName="Helvetica", fontSize=9.2, leading=12.6, leftIndent=16,
                  spaceAfter=0),
    }


S = styles()


# --------------------------------------------------------------- flowables
class Section(Paragraph):
    """H1 that registers itself in the table of contents."""

    def __init__(self, text, number=None):
        label = f"{number}. {text}" if number else text
        super().__init__(label, S["h1"])
        self._toc_text = label

    def notify_toc(self, doc):
        doc.notify("TOCEntry", (0, self._toc_text, doc.page))


class Sub(Paragraph):
    def __init__(self, text, number=None):
        label = f"{number} {text}" if number else text
        super().__init__(label, S["h2"])
        self._toc_text = label

    def notify_toc(self, doc):
        doc.notify("TOCEntry", (1, self._toc_text, doc.page))


def P(text):
    return Paragraph(text, S["body"])


def B(items):
    return [Paragraph(i, S["bullet"], bulletText="\u2022") for i in items]


def code(text, caption=None):
    """Monospace block with a light background, for diagrams and listings."""
    body = Preformatted(text, S["code"])
    box = Table([[body]], colWidths=[BODY_W])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    out = [box]
    if caption:
        out.append(Paragraph(caption, S["caption"]))
    else:
        out.append(Spacer(1, 8))
    return out


def esc(text: str) -> str:
    """
    Escape a bare ampersand for reportlab's mini-markup.

    "R&D" renders as "R&D;" because the parser reads "&D;" as a malformed entity.
    Only bare ampersands are escaped, so intentional markup such as <b> and <i>
    in table cells continues to work.
    """
    import re
    return re.sub(r"&(?!#?\w+;)", "&amp;", str(text))


def table(rows, widths, caption=None, header=True):
    data = []
    for r_index, row in enumerate(rows):
        line = []
        for cell in row:
            if isinstance(cell, Paragraph):
                line.append(cell)
            else:
                line.append(Paragraph(esc(cell),
                                      S["tabh"] if (header and r_index == 0) else S["tabc"]))
        data.append(line)
    t = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.6),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), LIGHT))
    t.setStyle(TableStyle(style))
    out = [t]
    if caption:
        out.append(Paragraph(caption, S["caption"]))
    else:
        out.append(Spacer(1, 8))
    return out


def callout(title, text, colour=ACCENT2):
    inner = [
        Paragraph(f"<b>{title}</b>", ParagraphStyle("ct", fontName="Helvetica-Bold",
                                                    fontSize=9.4, leading=12.6, textColor=colour)),
        Paragraph(text, ParagraphStyle("cb", fontName="Helvetica", fontSize=9.2, leading=12.6,
                                       alignment=TA_JUSTIFY)),
    ]
    box = Table([[inner]], colWidths=[BODY_W])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbf7ef")),
        ("LINEBEFORE", (0, 0), (0, -1), 2.2, colour),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2d9c8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [box, Spacer(1, 9)]


class Report(BaseDocTemplate):
    """Doc template that renders the TOC, page numbers and running header."""

    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        self.report_title = "SecondBrain Development Report"

    def afterFlowable(self, flowable):
        if hasattr(flowable, "notify_toc"):
            flowable.notify_toc(self)

    def header_footer(self, canvas, doc):
        canvas.saveState()
        # running header (not on the title page)
        if doc.page > 1:
            canvas.setFont("Helvetica", 7.6)
            canvas.setFillColor(GREY)
            canvas.drawString(MARGIN_X, PAGE_H - MARGIN_TOP + 22, self.report_title)
            canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP + 22,
                                   "SecondBrain  \u00b7  Adaptive Personal Memory")
            canvas.setStrokeColor(RULE)
            canvas.setLineWidth(0.4)
            canvas.line(MARGIN_X, PAGE_H - MARGIN_TOP + 17, PAGE_W - MARGIN_X, PAGE_H - MARGIN_TOP + 17)
        # footer
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GREY)
        canvas.drawCentredString(PAGE_W / 2.0, 30, str(doc.page))
        canvas.restoreState()
