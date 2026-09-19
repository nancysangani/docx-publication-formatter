# docx-publication-formatter
**Intelligent Machine Learning-Based Offline DOCX-to-Publication Book Formatting System**

## Quick Start (Windows)

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5055` in a browser. The UI runs on the local machine only.

For the CLI formatter:

```powershell
python cli.py samples\sample_unformatted.docx output.docx
```

Build the Windows CLI executable before a live demo with `./build_exe.bat`.
The executable packages the CLI; run the local web UI separately with `python app.py`.

## Problem Statement
Book publishers, academic institutions, and conference organizers frequently receive manuscripts as unformatted Microsoft Word (`.docx`) files. Editorial teams must manually apply formatting standards — a slow, resource-heavy process that introduces inconsistency across publications, especially at scale (400+ page documents).
## Objective
Build a fully **offline**, ML-based system that automatically detects structural elements in an unformatted `.docx` manuscript — titles, headings, subheadings, body text, tables, figures, captions, references, and lists — and applies a predefined publication formatting specification without rewriting paragraph or table text.
> **Constraint:** No Generative AI, LLMs, or cloud-based AI services are used anywhere in this pipeline. Classification uses an explainable, local Random Forest with deterministic rules.
## Approach
Instead of treating the manuscript as an image (OCR-style), this system reads the `.docx` file's native OOXML structure directly — every paragraph already carries machine-readable metadata (font size, boldness, alignment, indentation), which is exploited instead of guessed at.


Upload → Structure Parser → ML Classifier → Formatting Engine → Integrity Validator → Export


| Stage | What it does |
|---|---|
| **Structure Parser** | Extracts paragraphs, runs, and styles via the OOXML object model (`python-docx`, `lxml`) |
| **ML Classifier** | Tags each paragraph — Title, Heading, Body, Caption, Reference, Table, List — using a deterministic rule-based layer coupled with an engineered feature pipeline (font size, bold/italic, indentation, position, regex cues) feeding a local Random Forest classifier |
| **Formatting Engine** | Applies the exact publication spec deterministically per element type |
| **Integrity Validator** | Re-parses the DOCX output and compares normalized extracted body/table text block-by-block and with SHA-256 |

## Publication Formatting Spec

- Font: Times New Roman, 12pt, Black
- Alignment: Justified · Line spacing: 1.5 · First-line indent: 1.27 cm
- Margins: Top/Bottom 1.52 cm, Left 1.97 cm, Right 1.96 cm
- Heading 1: 16pt Bold · Subheading: 12pt Bold

## Tech Stack

| Component | Tool |
|---|---|
| Core language | Python 3 |
| Document parsing | `python-docx`, `lxml` |
| ML classification | `scikit-learn` (Random Forest) + deterministic rules |
| Formatting engine | `python-docx` style injection |
| Integrity validation | `hashlib` + custom text-diff module |
| Local UI | Flask + HTML/CSS/JavaScript |
| Testing | `pytest` |
| PDF extraction | `pdfplumber` (local text/layout extraction) |
| Packaging | PyInstaller CLI executable |

## Verified Performance

Benchmarked against the generated 420-page synthetic manuscript (~115,000 words and 4,000 blocks):

| Metric | Result |
|---|---|
| Total processing time | **~15.4 seconds** end-to-end on the measured machine; timing varies by hardware |
| Content integrity | **0 normalized extracted-text mismatches** in the measured run |
| Elements flagged for manual review | **0** in the measured generated sample |
| Embedded images/figures | **Preserved** — formatting is applied in place on the original document's paragraph/run/table objects, not by rebuilding from extracted text, so anything not explicitly restyled (images, drawings) survives untouched |

Run it yourself:
- `pytest tests/test_pipeline.py::test_scales_to_400_plus_pages`
- `pytest tests/test_pipeline.py::test_embedded_images_are_preserved`

**Offline executable verified working** — built with PyInstaller (`pyinstaller --onefile cli.py --name docx-formatter`), tested standalone with no Python interpreter or dependencies required at runtime.

## Build Roadmap

- [x] **Phase 1 — Structure Parser + Formatting Engine**  
      Parses native OOXML structure and applies the full publication spec end-to-end.
- [x] **Phase 2 — ML Classifier**  
      Hybrid rule + Random Forest classifier built, with confidence-based flagging for low-certainty predictions. 
- [x] **Phase 3 — Integrity Validator + Scale Testing**  
      Normalized extracted-text validator passing on all test manuscripts, including a generated 420-page stress test — verified via automated pytest.
- [x] **Phase 3.5 — Local UI**  
      Drag-and-drop interface with an automated tally and a live proof sheet showing per-element confidence scores and classifications.
- [x] **Phase 3.6 — Offline Executable**  
      Standalone binary built and verified via PyInstaller — runs with zero system dependencies.
- [x] **Phase 4 — Stress Testing & Rule Expansion**  
      Expanded the layout heuristic interpreter layer to generalize against adversarial formatting (mixed case sizes, short lines of dialogue, bracketed signatures) without breaking high-confidence thresholds.
- [x] **Phase 5 — PDF Input Support**
      Integrated local geometric PDF text/layout extraction and reconstruction into a formatted DOCX.

## Known Limitations (honest, as of this submission)

- The core ML classifier relies on a synthetic bootstrap configuration for its fallback layer. Manuscripts with non-standard fonts or unique structural conventions can still reach the low-certainty warning pipeline.
- Complex real-world table edge cases (such as deeply nested multi-level cell merges or tracked revision states) require additional edge-case testing to ensure layout styling parameters remain pristine.
- The PDF path reconstructs a new DOCX from locally extracted text. It does not preserve the original PDF's exact layout, images, annotations, or non-text objects; its integrity report applies to the reconstructed DOCX pipeline.
- The Office add-in manifest and local classification server are experimental integration artifacts and are not yet a production-verified Word add-in.

## Why This Approach

- **Structure-aware, not OCR-based** — uses the `.docx` format's own machine-readable metadata instead of visual/image-based guessing
- **Explainable Architecture** — combines deterministic structural rules with a shallow tree model; every classification choice can be traced back directly to clear typographical features rather than an uncontrollable black box
- **Integrity checked** — the validator compares normalized extracted body/table text after re-parsing the DOCX output
- **Fully offline** — no network calls, no cloud AI latency, no data privacy risk for unpublished manuscripts

## License

This project is licensed under the MIT License - see the LICENSE file for details.
