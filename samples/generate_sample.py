"""
Generates a deliberately messy, unformatted sample manuscript (.docx) —
mixed fonts, inconsistent sizes, no indentation discipline — to demo the
formatting pipeline against. This simulates the kind of raw submission a
publisher would actually receive.
"""

import os
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT_PATH = os.path.join(os.path.dirname(__file__), "sample_unformatted.docx")

CHAPTERS = [
    ("Chapter 1: The Beginning", [
        "It was a quiet morning when everything changed. The village lay still, unaware of the events "
        "that would soon unfold across its narrow streets and old stone houses.",
        "Marta had lived there her whole life, and never once had she imagined leaving. But the letter "
        "in her hand said otherwise, and its words would not let her rest.",
    ]),
    ("Chapter 2: The Journey", [
        "The road out of the village wound through hills that had not changed in a hundred years. "
        "Marta walked slowly, her bag heavier with every step.",
        "By nightfall she reached the crossroads mentioned in the letter, unsure of which path to take.",
    ]),
]

CAPTIONS = ["Fig. 1 Map of the village and surrounding hills", "Table 1 Travel times between key locations"]
REFERENCES = [
    "[1] Smith, J. (2019). Rural Migration Patterns. Oxford Press.",
    "[2] Doe, A. (2021). The Hidden Village. Cambridge Books.",
    "[3] Lee, K. (2020). Letters and Journeys. Penguin.",
]


def generate():
    doc = Document()

    # Title — inconsistent, oversized, left-aligned (typical raw manuscript mistake)
    p = doc.add_paragraph()
    run = p.add_run("The Hidden Village")
    run.font.size = Pt(24)
    run.font.bold = True
    run.font.name = "Arial"

    for chapter_title, paragraphs in CHAPTERS:
        p = doc.add_paragraph()
        run = p.add_run(chapter_title)
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.name = "Calibri"

        for para_text in paragraphs:
            p = doc.add_paragraph()
            run = p.add_run(para_text)
            run.font.size = Pt(11)
            run.font.name = "Calibri"
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT  # inconsistent — should be justified

        # a caption dropped in with no special styling at all
        p = doc.add_paragraph()
        run = p.add_run(CAPTIONS.pop(0) if CAPTIONS else "Fig. X Untitled")
        run.font.size = Pt(10)
        run.font.italic = True
        run.font.name = "Calibri"

    # A raw, unstyled table
    table = doc.add_table(rows=3, cols=2)
    data = [["Location", "Distance (km)"], ["Village", "0"], ["Crossroads", "14"]]
    for r, row in enumerate(data):
        for c, val in enumerate(row):
            table.cell(r, c).text = val

    # References, inconsistently formatted
    p = doc.add_paragraph()
    run = p.add_run("References")
    run.font.size = Pt(14)
    run.font.bold = True

    for ref in REFERENCES:
        p = doc.add_paragraph()
        run = p.add_run(ref)
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

    doc.save(OUT_PATH)
    print(f"Sample manuscript written to {OUT_PATH}")


if __name__ == "__main__":
    generate()
