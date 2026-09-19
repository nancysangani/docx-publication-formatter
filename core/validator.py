"""
Integrity Validator
--------------------
Formatting a manuscript is worthless — dangerous, even — if it silently
changes the author's words. This module re-parses the formatted output and
compares its extracted body and table text with the original, block by block,
with a checksum over the normalized extracted text as a final cross-check.
"""

import hashlib
from core.parser import parse_docx, extract_plain_text


def _normalize(text):
    """Whitespace-insensitive normalization.

    Formatting may change layout whitespace, but it must not change extracted
    body or table words. Headers, footers, comments, footnotes, and tracked
    changes are outside this validator's current scope.
    """
    return " ".join(text.split())


def _checksum(text):
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()


def validate(original_blocks, formatted_output_path):
    """Compare original parsed blocks against the freshly-formatted output.
    Returns a report dict with pass/fail status and a per-block diff."""
    _, formatted_blocks = parse_docx(formatted_output_path)

    original_texts = [_normalize(b["text"]) for b in original_blocks]
    formatted_texts = [_normalize(b["text"]) for b in formatted_blocks]

    mismatches = []
    max_len = max(len(original_texts), len(formatted_texts))
    for i in range(max_len):
        orig = original_texts[i] if i < len(original_texts) else None
        fmt = formatted_texts[i] if i < len(formatted_texts) else None
        if orig != fmt:
            mismatches.append({"block_index": i, "original": orig, "formatted": fmt})

    original_checksum = _checksum(extract_plain_text(original_blocks))
    formatted_checksum = _checksum(extract_plain_text(formatted_blocks))

    passed = len(mismatches) == 0 and original_checksum == formatted_checksum

    return {
        "passed": passed,
        "total_blocks": len(original_texts),
        "mismatched_blocks": len(mismatches),
        "mismatches": mismatches[:20],  # cap for readability
        "original_checksum": original_checksum,
        "formatted_checksum": formatted_checksum,
    }
