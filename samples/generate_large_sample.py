"""
Generates a large, unformatted synthetic manuscript sized to approximate the
brief's 400+ page scalability requirement, so the pipeline's timing and
memory behavior can be measured against a real number instead of a guess.

Sizing rationale: at 12pt Times New Roman with the spec's margins/spacing,
a typical page holds roughly 250-300 words. Targeting ~400 pages means
~100,000-120,000 words, which this script reaches by generating many
short "chapters" in the same style as the small demo sample.
"""

import os
import random
from docx import Document
from docx.shared import Pt

OUT_PATH = os.path.join(os.path.dirname(__file__), "sample_large_manuscript.docx")

WORDS = ("the village lay quiet beneath a pale morning sky while distant hills held "
         "their old secrets and the narrow road wound onward past fields long since "
         "abandoned by those who once tended them with careful hands and patient hope "
         "every traveler who passed that way carried a story of their own some spoke of "
         "war others of loss and a few of nothing but the weather yet all agreed the "
         "crossroads ahead would decide which path their fortune finally took").split()


def _random_paragraph(rng, min_words=25, max_words=45):
    n = rng.randint(min_words, max_words)
    words = [rng.choice(WORDS) for _ in range(n)]
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def generate(target_pages=420, seed=7):
    rng = random.Random(seed)
    doc = Document()

    # ~275 words/page target; ~5 paragraphs of ~35 words + heading overhead per "page equivalent"
    words_per_page = 275
    target_words = target_pages * words_per_page
    words_written = 0
    chapter_num = 1

    while words_written < target_words:
        p = doc.add_paragraph()
        run = p.add_run(f"Chapter {chapter_num}: Fragment {chapter_num}")
        run.font.size = Pt(16)
        run.font.bold = True
        words_written += 3

        n_paragraphs = rng.randint(4, 7)
        for _ in range(n_paragraphs):
            text = _random_paragraph(rng)
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.size = Pt(11)
            words_written += len(text.split())

        if chapter_num % 4 == 0:
            p = doc.add_paragraph()
            run = p.add_run(f"Fig. {chapter_num // 4} Illustration referenced in chapter {chapter_num}")
            run.font.size = Pt(10)
            run.font.italic = True
            words_written += 6

        chapter_num += 1

    # A references section at the end
    p = doc.add_paragraph()
    run = p.add_run("References")
    run.font.size = Pt(14)
    run.font.bold = True
    for i in range(1, 30):
        p = doc.add_paragraph()
        run = p.add_run(f"[{i}] Author {i}, A. ({2000 + i}). Sample Reference Title {i}. Publisher House.")
        run.font.size = Pt(10)

    doc.save(OUT_PATH)
    print(f"Large manuscript written to {OUT_PATH} — {chapter_num} chapters, ~{words_written} words "
          f"(~{words_written // words_per_page} estimated pages)")
    return OUT_PATH


if __name__ == "__main__":
    generate()
