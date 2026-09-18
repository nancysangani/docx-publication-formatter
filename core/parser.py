"""
Structure Parser
----------------
Reads a .docx file's native OOXML structure directly (no OCR, no guessing).
Every paragraph in a .docx already carries machine-readable metadata: font
size, boldness, alignment, indentation. This module extracts that metadata
into a list of "blocks" that downstream stages (classifier, formatter,
validator) operate on.

Each block is a dict:
{
    "index": int,             # position in the document (0-based)
    "type": "paragraph"|"table",
    "text": str,              # exact original text, never modified
    "font_size": float|None,  # in points
    "bold": bool,
    "italic": bool,
    "alignment": str,         # "left"|"center"|"right"|"justify"|None
    "indent_cm": float,       # left indent in cm, 0 if none
    "is_all_caps": bool,
    "starts_with_number": bool,
    "word_count": int,
    "table_data": list|None,  # only for type == "table"
}
"""

from docx import Document
from docx.shared import Pt, Cm
import re

NUMBERED_PATTERN = re.compile(r"^\s*(chapter|section|part)\s+\d+", re.IGNORECASE)
FIG_TABLE_PATTERN = re.compile(r"^\s*(fig\.?|figure|table)\s*\d*", re.IGNORECASE)
REFERENCE_PATTERN = re.compile(r"^\s*(\[\d+\]|\d+\.)\s")


def _emu_to_cm(emu):
    if emu is None:
        return 0.0
    return round(emu / 360000, 3)  # 1 cm = 360000 EMU


def _paragraph_font_info(paragraph):
    """Get the dominant font size / bold / italic across a paragraph's runs."""
    sizes, bolds, italics = [], [], []
    for run in paragraph.runs:
        if run.font.size is not None:
            sizes.append(run.font.size.pt)
        if run.font.bold:
            bolds.append(True)
        if run.font.italic:
            italics.append(True)

    # Fall back to paragraph style font size if no run-level size is set
    if not sizes and paragraph.style and paragraph.style.font.size:
        sizes.append(paragraph.style.font.size.pt)

    font_size = max(sizes) if sizes else None
    is_bold = len(bolds) > 0 and len(bolds) >= len(paragraph.runs) / 2
    is_italic = len(italics) > 0 and len(italics) >= len(paragraph.runs) / 2
    return font_size, is_bold, is_italic


def _alignment_name(paragraph):
    align = paragraph.alignment
    if align is None:
        return None
    return str(align).split(".")[-1].lower()  # e.g. "JUSTIFY" -> "justify"


def parse_docx(path):
    """
    Parse a .docx file and return (document, blocks).
    `document` is the python-docx Document object (kept for the formatter
    stage to reuse); `blocks` is the extracted structure list.
    """
    doc = Document(path)
    blocks = []
    index = 0

    # Walk the document body in order, handling paragraphs and tables.
    body = doc.element.body
    para_map = {p._p: p for p in doc.paragraphs}
    table_map = {t._tbl: t for t in doc.tables}

    for child in body.iterchildren():
        if child.tag.endswith("}p") and child in para_map:
            paragraph = para_map[child]
            text = paragraph.text.strip()
            if text == "":
                continue
            font_size, is_bold, is_italic = _paragraph_font_info(paragraph)
            indent_cm = _emu_to_cm(
                paragraph.paragraph_format.left_indent.emu
                if paragraph.paragraph_format.left_indent else None
            )
            blocks.append({
                "index": index,
                "type": "paragraph",
                "text": text,
                "font_size": font_size,
                "bold": is_bold,
                "italic": is_italic,
                "alignment": _alignment_name(paragraph),
                "indent_cm": indent_cm,
                "is_all_caps": text.isupper() and len(text) > 1,
                "starts_with_number": bool(NUMBERED_PATTERN.match(text) or REFERENCE_PATTERN.match(text)),
                "starts_with_fig_table": bool(FIG_TABLE_PATTERN.match(text)),
                "word_count": len(text.split()),
                "table_data": None,
                "_paragraph_ref": paragraph,
            })
            index += 1
        elif child.tag.endswith("}tbl") and child in table_map:
            table = table_map[child]
            data = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            blocks.append({
                "index": index,
                "type": "table",
                "text": "\n".join(" | ".join(r) for r in data),
                "font_size": None,
                "bold": False,
                "italic": False,
                "alignment": None,
                "indent_cm": 0,
                "is_all_caps": False,
                "starts_with_number": False,
                "starts_with_fig_table": False,
                "word_count": sum(len(c.split()) for row in data for c in row),
                "table_data": data,
                "_paragraph_ref": None,
                "_table_ref": table,
            })
            index += 1

    return doc, blocks


def extract_plain_text(blocks):
    """Flatten blocks to a single plain-text stream — used by the Integrity
    Validator to compare pre/post formatting content, independent of style."""
    lines = []
    for b in blocks:
        if b["type"] == "table":
            for row in b["table_data"]:
                lines.append(" | ".join(row))
        else:
            lines.append(b["text"])
    return "\n".join(lines)
