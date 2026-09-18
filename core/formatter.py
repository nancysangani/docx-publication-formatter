"""
Formatting Engine
-----------------
Takes the classified blocks and applies the exact publication specification
per element type, DIRECTLY ON THE ORIGINAL DOCUMENT — it does not rebuild a
new .docx from scratch. This matters: a manuscript's paragraphs can contain
embedded images, drawings, hyperlinks, or other objects living inside the
paragraph's own XML. Rebuilding paragraphs from extracted text alone would
silently drop anything that isn't plain text. Styling the existing
paragraph/run objects in place means anything we don't explicitly touch is
preserved automatically — which is what "preserve all original content"
actually requires when a manuscript has figures in it, not just words.

CRITICAL RULE: this stage NEVER rewrites, paraphrases, or alters a single
character of any run's text. Only *style* properties are set.
"""

from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

FONT_NAME = "Times New Roman"
BLACK = RGBColor(0, 0, 0)

# Publication spec, from the problem statement
MARGINS_CM = {"top": 1.52, "bottom": 1.52, "left": 1.97, "right": 1.96}
BODY_SIZE = 12
HEADING_SIZE = 16
SUBHEADING_SIZE = 12
TITLE_SIZE = 20
CAPTION_SIZE = 10
REFERENCE_SIZE = 11
LIST_SIZE = 11
TABLE_SIZE = 11
LINE_SPACING = 1.5
FIRST_LINE_INDENT_CM = 1.27


STYLE_RULES = {
    "Title": dict(size=TITLE_SIZE, bold=True, align="center", indent=False),
    "Heading": dict(size=HEADING_SIZE, bold=True, align="left", indent=False),
    "Subheading": dict(size=SUBHEADING_SIZE, bold=True, align="left", indent=False),
    "Body": dict(size=BODY_SIZE, bold=False, align="justify", indent=True),
    "Caption": dict(size=CAPTION_SIZE, bold=False, italic=True, align="center", indent=False),
    "Reference": dict(size=REFERENCE_SIZE, bold=False, align="left", indent=False, hanging=True),
    "List": dict(size=LIST_SIZE, bold=False, align="left", indent=False, bullet=True),
}

ALIGN_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _set_margins(doc):
    for section in doc.sections:
        section.top_margin = Cm(MARGINS_CM["top"])
        section.bottom_margin = Cm(MARGINS_CM["bottom"])
        section.left_margin = Cm(MARGINS_CM["left"])
        section.right_margin = Cm(MARGINS_CM["right"])
        try:
            section.gutter = Cm(0.5)  # gutter position: left (default binding side)
        except Exception:
            pass


def _apply_paragraph_style(paragraph, rule):
    fmt = paragraph.paragraph_format
    fmt.line_spacing = LINE_SPACING
    fmt.alignment = ALIGN_MAP.get(rule.get("align", "left"), WD_ALIGN_PARAGRAPH.LEFT)
    fmt.first_line_indent = None
    fmt.left_indent = None

    if rule.get("indent"):
        fmt.first_line_indent = Cm(FIRST_LINE_INDENT_CM)
    if rule.get("hanging"):
        fmt.left_indent = Cm(1.0)
        fmt.first_line_indent = Cm(-1.0)
    if rule.get("bullet"):
        fmt.left_indent = Cm(0.8)


def _style_existing_runs(paragraph, rule):
    """Style every run already in the paragraph — never removes or replaces
    a run, so any drawing/image/hyperlink content inside a run's XML is left
    untouched. A paragraph with zero runs (rare, but possible) is left as-is."""
    for run in paragraph.runs:
        run.font.name = FONT_NAME
        run.font.size = Pt(rule["size"])
        run.font.bold = rule.get("bold", False)
        run.font.italic = rule.get("italic", False)
        run.font.color.rgb = BLACK


def apply_formatting_in_place(doc, classified_blocks):
    """Applies the publication spec directly onto the original document's
    paragraph/run/table objects. Returns the same `doc`, now formatted."""
    _set_margins(doc)

    for block in classified_blocks:
        label = block["label"]

        if label == "Table":
            table = block.get("_table_ref")
            if table is None:
                continue
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        p.paragraph_format.line_spacing = LINE_SPACING
                        for run in p.runs:
                            run.font.name = FONT_NAME
                            run.font.size = Pt(TABLE_SIZE)
                            run.font.color.rgb = BLACK
            continue

        paragraph = block.get("_paragraph_ref")
        if paragraph is None:
            continue
        rule = STYLE_RULES.get(label, STYLE_RULES["Body"])
        _apply_paragraph_style(paragraph, rule)
        _style_existing_runs(paragraph, rule)

    return doc


def save_formatted_document(doc, classified_blocks, output_path):
    apply_formatting_in_place(doc, classified_blocks)
    doc.save(output_path)
    return output_path
