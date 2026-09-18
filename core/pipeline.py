"""
End-to-end pipeline: Upload -> Parse -> Classify -> Format -> Validate -> Export
"""

import time
from core.parser import parse_docx
from core.classifier import ElementClassifier
from core.formatter import save_formatted_document
from core.validator import validate

_classifier = None


def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ElementClassifier()
    return _classifier


def run_pipeline(input_path, output_path):
    timings = {}

    t0 = time.time()
    doc, blocks = parse_docx(input_path)
    timings["parse_seconds"] = round(time.time() - t0, 3)

    t0 = time.time()
    classifier = get_classifier()
    classified = classifier.classify_all(blocks)
    timings["classify_seconds"] = round(time.time() - t0, 3)

    t0 = time.time()
    # Format the SAME document object we parsed and classified against —
    # classified blocks hold direct references (_paragraph_ref/_table_ref)
    # into this doc's actual paragraph/table objects, so formatting applies
    # in place and anything we don't touch (images, embedded objects) is
    # preserved automatically.
    save_formatted_document(doc, classified, output_path)
    timings["format_seconds"] = round(time.time() - t0, 3)

    t0 = time.time()
    integrity_report = validate(blocks, output_path)
    timings["validate_seconds"] = round(time.time() - t0, 3)

    label_counts = {}
    review_flags = []
    for b in classified:
        label_counts[b["label"]] = label_counts.get(b["label"], 0) + 1
        if b["needs_review"]:
            review_flags.append({
                "index": b["index"],
                "text_preview": b["text"][:80],
                "label": b["label"],
                "confidence": b["confidence"],
            })

    return {
        "blocks": classified,
        "label_counts": label_counts,
        "review_flags": review_flags,
        "integrity": integrity_report,
        "timings": timings,
        "output_path": output_path,
    }
