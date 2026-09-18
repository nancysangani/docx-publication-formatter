#!/usr/bin/env python3
"""
CLI usage:
    python cli.py <input.docx> <output.docx>
    python cli.py --server
    python cli.py <input.pdf>

Runs the full offline pipeline: Parse -> Classify -> Format -> Validate,
and prints a summary report (element counts, low-confidence flags, and the
integrity check result).
"""

import sys
import json
import os
from core.pipeline import run_pipeline

# Phase 5 Architecture Modules
from core.server import run_server
from core.pdf_parser import convert_pdf_to_pipeline_blocks


def main():
    args = sys.argv[1:]

    # -----------------------------------------------------------------
    # INTEGRATION 1: Background Local Microservice API Server Routing
    # -----------------------------------------------------------------
    if "--server" in args:
        print("\n=== Activating Microservice Engine ===")
        run_server(port=8080)
        return

    # Ensure correct basic usage check if not running the server
    if len(args) < 1:
        print("Usage: python cli.py <input.docx> <output.docx>  OR  python cli.py --server  OR  python cli.py <input.pdf>")
        sys.exit(1)

    input_path = args[0]

    # -----------------------------------------------------------------
    # INTEGRATION 2: Upstream PDF Geometric Ingestion In-Memory Inflow
    # -----------------------------------------------------------------
    if input_path.lower().endswith(".pdf"):
        print("\n=== Initializing Geometric Offline Ingestion Engine ===")
        print(f"Ingesting PDF vector canvas: {input_path}")
        
        # Verify file existence locally
        if not os.path.exists(input_path):
            print(f"Error: File not found at {input_path}")
            sys.exit(1)
            
        doc_ref, blocks = convert_pdf_to_pipeline_blocks(input_path)
        print(f"Successfully extracted {len(blocks)} layout blocks from raw layout coordinates.")
        print("PDF data conversion structurally ready. Downstream classification vector available.")
        print("\n=== PDF Dry-Run Parsing Simulation Passing with Success ✅ ===")
        return

    # -----------------------------------------------------------------
    # BASELINE: Standard Production DOCX Execution Core Pathway
    # -----------------------------------------------------------------
    if len(sys.argv) != 3:
        print("Usage: python cli.py <input.docx> <output.docx>")
        sys.exit(1)

    output_path = sys.argv[2]
    result = run_pipeline(input_path, output_path)

    print("\n=== Formatting Complete ===")
    print(f"Output written to: {result['output_path']}\n")

    print("Element classification counts:")
    for label, count in sorted(result["label_counts"].items(), key=lambda x: -x[1]):
        print(f"  {label:<12} {count}")

    print(f"\nElements flagged for manual review (confidence < 0.55): {len(result['review_flags'])}")
    for flag in result["review_flags"]:
        print(f"  [#{flag['index']}] \"{flag['text_preview']}...\" -> {flag['label']} ({flag['confidence']})")

    print("\nIntegrity Validation:")
    integ = result["integrity"]
    status = "PASSED ✅" if integ["passed"] else "FAILED ❌"
    print(f"  Status: {status}")
    print(f"  Blocks compared: {integ['total_blocks']}  |  Mismatches: {integ['mismatched_blocks']}")
    print(f"  Original checksum:  {integ['original_checksum'][:16]}...")
    print(f"  Formatted checksum: {integ['formatted_checksum'][:16]}...")

    print("\nTimings:")
    for k, v in result["timings"].items():
        print(f"  {k}: {v}s")


if __name__ == "__main__":
    main()
