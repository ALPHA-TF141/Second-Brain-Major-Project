#!/usr/bin/env python3
"""Build docs/diagrams/paper_architecture_editable.docx.

The architecture figure as NATIVE Word shapes (DrawingML group), so every
box, connector and label can be selected, dragged, recoloured and retyped
inside Microsoft Word. Geometry mirrors paper_architecture.svg
(1 SVG px = 9525 EMU). Stdlib only.
"""
import zipfile

EMU = 9525  # per svg px


def px(v):
    return int(round(v * EMU))


def pt2half(pt):
    return int(round(pt * 2))


SHAPES = []
_sid = [10]


def nid():
    _sid[0] += 1
    return _sid[0]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, lines, fill="F2F2F2", line="333333", lw=7620, dash=None,
        nofill=False):
    """lines: list of (text, pt, bold, italic)."""
    i = nid()
    ln = f'<a:ln w="{lw}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill>'
    ln += f'<a:prstDash val="{dash}"/>' if dash else ""
    ln += "</a:ln>"
    fl = '<a:noFill/>' if nofill else f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
    paras = ""
    for (t, sz, b, it) in lines:
        paras += (
            '<w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
            '<w:jc w:val="center"/></w:pPr><w:r><w:rPr>'
            f'<w:i w:val="{1 if it else 0}"/><w:b w:val="{1 if b else 0}"/>'
            f'<w:sz w:val="{pt2half(sz)}"/><w:szCs w:val="{pt2half(sz)}"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>'
        )
    SHAPES.append(f"""<wpg:wsp><wpg:cNvPr id="{i}" name="Box{i}"/><wpg:cNvSpPr/>
<wps:spPr><a:xfrm><a:off x="{px(x)}" y="{px(y)}"/><a:ext cx="{px(w)}" cy="{px(h)}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fl}{ln}</wps:spPr>
<wps:txbx><w:txbxContent>{paras}</w:txbxContent></wps:txbx>
<wps:bodyPr rot="0" spcFirst="0" spcSub="0" anchor="ctr" anchorCtr="0" lIns="9525" tIns="0" rIns="9525" bIns="0" wrap="square"><a:noAutofit/></wps:bodyPr></wpg:wsp>""")


def textbox(x, y, w, h, t, sz, it=False, b=False):
    box(x, y, w, h, [(t, sz, b, it)], nofill=True, lw=0, line="FFFFFF")
    # strip the invisible line: replace ln of last shape
    SHAPES[-1] = SHAPES[-1].replace(
        '<a:ln w="0"><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:ln>',
        '<a:ln><a:noFill/></a:ln>')


def conn(x1, y1, x2, y2, arrow=False, dash=None, lw=7620):
    i = nid()
    offx, offy = min(x1, x2), min(y1, y2)
    extx, exty = abs(x2 - x1), abs(y2 - y1)
    flip = ""
    if x2 < x1:
        flip += ' flipH="1"'
    if y2 < y1:
        flip += ' flipV="1"'
    if extx == 0:
        extx = 0
    if exty == 0:
        exty = 0
    d = f'<a:prstDash val="{dash}"/>' if dash else ""
    tail = '<a:tailEnd type="triangle" w="med" len="med"/>' if arrow else ""
    SHAPES.append(f"""<wpg:wsp><wpg:cNvPr id="{i}" name="Line{i}"/><wpg:cNvSpPr/>
<wps:spPr><a:xfrm{flip}><a:off x="{px(offx)}" y="{px(offy)}"/><a:ext cx="{px(extx)}" cy="{px(exty)}"/></a:xfrm>
<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:noFill/>
<a:ln w="{lw}"><a:solidFill><a:srgbClr val="333333"/></a:solidFill>{d}{tail}</a:ln></wps:spPr>
<wps:bodyPr/></wpg:wsp>""")


# ---------------- geometry (mirrors paper_architecture.svg) ----------------
L = [("Capture & ingest", 7.1, True, False), ("screen OCR · mail · web · voice · clipboard", 5.2, False, False)]
box(6, 6, 160, 32, L)
box(6, 50, 160, 32, [("Normalisation", 7.1, True, False), ("chunking · content hash · dedup key", 5.2, False, False)])
box(6, 94, 160, 32, [("Memory store", 7.1, True, False), ("SQLite · FTS index · vectors · derived graph", 5.2, False, False)])
box(6, 138, 160, 32, [("Retrieval", 7.1, True, False), ("vanilla · hybrid · graph · adaptive", 5.2, False, False)], fill="E6E6E6", lw=12700)
box(6, 182, 160, 32, [("Generation", 7.1, True, False), ("local / hosted LLM over ranked context", 5.2, False, False)])

box(196, 6, 158, 154, [], nofill=True, lw=9525, dash="dash")
textbox(196, 10, 158, 10, "Research layer (additive, switchable)", 6.4, it=True)
for k, (yy, t) in enumerate([
        (25, "C1  Adaptive scoring · 8 terms"), (47, "C2  Temporal TKG · supersession"),
        (69, "C3  NLI conflicts · rank damping"), (91, "C4  Consolidation · provenance"),
        (113, "C5  Knowledge-gap detection"), (135, "C6  Forgetting · 5 surfaces")]):
    box(204, yy, 142, 19, [(t, 5.9, False, False)], fill="FFFFFF", line="555555", lw=6350)
box(196, 182, 158, 32, [("C7  PersonalBrain-Bench", 6.6, True, False),
                        ("evaluates the four pipelines (Tables III–VIII)", 5.2, False, False)], fill="FFFFFF")

conn(86, 38, 86, 45.5, arrow=True)
conn(86, 82, 86, 89.5, arrow=True)
conn(86, 126, 86, 133.5, arrow=True)
conn(86, 170, 86, 177.5, arrow=True)

conn(166, 104, 191, 104, arrow=True)
textbox(166, 92, 30, 8, "annotate", 4.7)
conn(196, 116, 171, 116, arrow=True)
textbox(166, 119, 30, 8, "scores", 4.7)

conn(210, 160, 210, 178)
conn(210, 178, 176, 178)
conn(176, 178, 176, 154)
conn(176, 154, 171, 154, arrow=True)
textbox(225, 167, 74, 8, "exclude · damp · dedup", 4.7)

conn(196, 198, 172, 198, dash="dash")
conn(172, 198, 172, 162, dash="dash")
conn(172, 162, 170, 162, arrow=True, dash="dash")
textbox(166, 201, 30, 8, "measures", 4.7)

W, H = px(360), px(222)
group = f"""<wpg:wgp><wpg:cNvGrpSpPr/><wpg:grpSpPr><a:xfrm><a:off x="0" y="0"/>
<a:ext cx="{W}" cy="{H}"/><a:chOff x="0" y="0"/><a:chExt cx="{W}" cy="{H}"/></a:xfrm></wpg:grpSpPr>
{''.join(SHAPES)}</wpg:wgp>"""

document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
<w:body>
<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{W}" cy="{H}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:docPr id="2" name="SecondBrain Architecture"/><wp:cNvGraphicFramePr/>
<a:graphic><a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">{group}</a:graphicData></a:graphic>
</wp:inline></w:drawing></w:r></w:p>
<w:p><w:pPr><w:spacing w:before="120"/></w:pPr><w:r><w:rPr><w:i/><w:sz w:val="18"/></w:rPr>
<w:t xml:space="preserve">Fig. 1 (editable). Every element above is a native Word shape: click a box or arrow to select it, drag to move, double-click text to retype, use Shape Format to recolour. Resize the whole figure via the group handles; all parts scale together.</w:t></w:r></w:p>
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>
</w:body></w:document>"""

styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Cambria" w:hAnsi="Cambria"/><w:sz w:val="22"/></w:rPr></w:rPrDefault>
<w:pPrDefault/></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style></w:styles>"""

ct = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

out = "paper_architecture_editable.docx"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ct)
    z.writestr("_rels/.rels", rels)
    z.writestr("word/document.xml", document)
    z.writestr("word/_rels/document.xml.rels", doc_rels)
    z.writestr("word/styles.xml", styles)
print("wrote", out, "| shapes:", len(SHAPES))
