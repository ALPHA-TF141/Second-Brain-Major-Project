"""
Build the complete SecondBrain development report as a PDF.
===========================================================================
  python generate_development_report.py   ->  SECOND_BRAIN_DEVELOPMENT_REPORT.pdf
"""
import sys

from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

from report_builder_base import (
    BODY_W, MARGIN_BOTTOM, MARGIN_TOP, MARGIN_X, OUT, PAGE_H, PAGE_W, Report, S,
)
import report_content_a
import report_content_b


def main():
    story = []
    story.extend(report_content_a.build())
    story.extend(report_content_b.build())

    doc = Report(
        OUT,
        pagesize=(PAGE_W, PAGE_H),
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title="SecondBrain Development Report",
        author="Dr. P S Anu Rakhi; Maria Immanuel L; Vigneshwaran S",
        subject="Complete development report: conception, architecture, deviations, defects, research",
    )

    frame = Frame(MARGIN_X, MARGIN_BOTTOM, BODY_W,
                  PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, id="body")
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=doc.header_footer)])

    # multiBuild resolves the table of contents across passes
    doc.multiBuild(story)

    print(f"[OK] wrote {OUT}")

    try:
        import pymupdf
        d = pymupdf.open(OUT)
        words = sum(len(d[i].get_text().split()) for i in range(d.page_count))
        print(f"     pages : {d.page_count}")
        print(f"     words : approximately {words:,}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
