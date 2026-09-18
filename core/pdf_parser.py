"""
PDF Structure Parser (Phase 5 Ingestion Module)
----------------------------------------------
Parses an unformatted geometric PDF layout completely offline using pdfplumber.
Extracts line coordinates and metadata to synthesize a structured dictionary block array,
matching the contract established in core/parser.py for full pipeline compatibility.
"""

import pdfplumber
import re

NUMBERED_PATTERN = re.compile(r"^\s*(chapter|section|part)\s+\d+", re.IGNORECASE)
FIG_TABLE_PATTERN = re.compile(r"^\s*(fig\.?|figure|table)\s*\d*", re.IGNORECASE)
REFERENCE_PATTERN = re.compile(r"^\s*(\[\d+\]|\d+\.)\s")

def convert_pdf_to_pipeline_blocks(pdf_path):
    """
    Parses a geometric PDF canvas layout and flattens it into structured block dict objects.
    Maintains 100% downstream style interface safety with classifier.py and validator.py.
    """
    extracted_blocks = []
    index = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract raw characters with visual coordinate dimensions
            words = page.extract_words(extra_attrs=["fontname", "size"])
            if not words:
                continue
                
            # Group isolated words into horizontal rows via proximity alignment thresholds
            lines = {}
            for w in words:
                top_coord = round(w["top"], 1)
                found = False
                for existing_top in lines:
                    if abs(existing_top - top_coord) < 4.0: # Same geometric baseline plane row
                        lines[existing_top].append(w)
                        found = True
                        break
                if not found:
                    lines[top_coord] = [w]
            
            # Map lines down the vertical axis canvas layout sequentially
            for top_y in sorted(lines.keys()):
                line_words = sorted(lines[top_y], key=lambda x: x["x0"])
                text = " ".join([w["text"] for w in line_words]).strip()
                
                if not text:
                    continue
                
                # Derive layout parameter signals
                avg_font_size = sum([w["size"] for w in line_words]) / len(line_words)
                is_bold = any("bold" in w["fontname"].lower() for w in line_words)
                is_italic = any("italic" in w["fontname"].lower() for w in line_words)
                
                # Convert canvas pt points into centimeter properties to align formats
                left_margin_pt = line_words[0]["x0"]
                base_margin_pt = 54.0 # Typical base margin baseline (0.75 in)
                indent_pt = max(0.0, left_margin_pt - base_margin_pt)
                indent_cm = round(indent_pt * 0.0352778, 3) # Convert typographical pt coordinates to cm
                
                # Map out elements matching the contract from core/parser.py
                extracted_blocks.append({
                    "index": index,
                    "type": "paragraph",
                    "text": text,
                    "font_size": round(avg_font_size, 1),
                    "bold": is_bold,
                    "italic": is_italic,
                    "alignment": "justify" if text.endswith('.') and len(text) > 60 else "left",
                    "indent_cm": indent_cm,
                    "is_all_caps": text.isupper() and len(text) > 1,
                    "starts_with_number": bool(NUMBERED_PATTERN.match(text) or REFERENCE_PATTERN.match(text)),
                    "starts_with_fig_table": bool(FIG_TABLE_PATTERN.match(text)),
                    "word_count": len(text.split()),
                    "table_data": None,
                    "_paragraph_ref": None # Kept None since PDF ingestion has no OOXML document context
                })
                index += 1
                
    return None, extracted_blocks
