"""
Build the complete multi-volume SecondBrain development report.
===========================================================================
  python generate_big_report.py  ->  SECOND_BRAIN_COMPLETE_REPORT.pdf
"""
from reportlab.lib.units import mm
from reportlab.platypus import Frame, PageTemplate, NextPageTemplate

from report_builder_base import (
    BODY_W, MARGIN_BOTTOM, MARGIN_TOP, MARGIN_X, PAGE_H, PAGE_W, Report,
)
import report2_content_1
import report2_content_2
import report2_content_3

OUT = "SECOND_BRAIN_COMPLETE_REPORT.pdf"


def main():
    story = []
    story.extend(report2_content_1.build())
    story.extend(report2_content_2.build())
    story.extend(report2_content_3.build())

    doc = Report(
        OUT,
        pagesize=(PAGE_W, PAGE_H),
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title="SecondBrain — Complete Engineering Record",
        author="Dr. P S Anu Rakhi; Maria Immanuel L; Vigneshwaran S",
        subject="Conception, architecture, deviations, defects and research contribution",
    )

    frame = Frame(MARGIN_X, MARGIN_BOTTOM, BODY_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, id="body")
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=doc.header_footer)])
    doc.report_title = "SecondBrain \u2014 Complete Engineering Record"
    doc.build(story)

    import os
    print(f"[OK] wrote {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")
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
