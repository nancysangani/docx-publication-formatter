# docx-publication-formatter

**Intelligent Machine Learning-Based Offline DOCX-to-Publication Book Formatting System**

---

## Problem Statement

Book publishers, academic institutions, and conference organizers frequently receive manuscripts as unformatted Microsoft Word (`.docx`) files. Editorial teams must manually apply formatting standards — a slow, resource-heavy process that introduces inconsistency across publications, especially at scale (400+ page documents).

## Objective

Build a fully **offline**, ML-based system that automatically detects structural elements in an unformatted `.docx` manuscript — titles, headings, subheadings, body text, tables, figures, captions, references, and lists — and applies a predefined publication formatting specification, while **preserving 100% of the original content** with zero rewriting or paraphrasing.

> **Constraint:** No Generative AI, LLMs, or cloud-based AI services are used anywhere in this pipeline. Classification relies entirely on classical, explainable ML (Random Forest / CRF) running locally.

## Approach

Instead of treating the manuscript as an image (OCR-style), this system reads the `.docx` file's native OOXML structure directly — every paragraph already carries machine-readable metadata (font size, boldness, alignment, indentation), which is exploited instead of guessed at.

```
Upload → Structure Parser → ML Classifier → Formatting Engine → Integrity Validator → Export
```

| Stage | What it does |
|---|---|
| **Structure Parser** | Extracts paragraphs, runs, and styles via the OOXML object model (`python-docx`, `lxml`) |
| **ML Classifier** | Tags each paragraph — Title, Heading, Body, Caption, Reference, Table, List — using engineered features (font size, bold/italic, indentation, position, regex cues) with Random Forest / CRF |
| **Formatting Engine** | Applies the exact publication spec deterministically per element type |
| **Integrity Validator** | Runs a pre/post checksum diff on extracted text to mathematically guarantee zero content change |

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
| ML classification | `scikit-learn` (Random Forest), `sklearn-crfsuite` (CRF) |
| Formatting engine | `python-docx` style injection |
| Integrity validation | `hashlib` + custom text-diff module |
| Desktop UI | PyQt / Electron |
| Testing | `pytest` |
| Packaging | PyInstaller (offline executable, no install dependencies) |

## Build Roadmap

- [ ] **Phase 1 — Structure Parser + Formatting Engine**
      Deterministic, lowest-risk components — parse OOXML structure and apply formatting rules end-to-end on a manually-labeled sample.
- [ ] **Phase 2 — ML Classifier**
      Build labeled training set from sample manuscripts; train and evaluate Random Forest / CRF classifier; add confidence-based flagging for low-certainty predictions.
- [ ] **Phase 3 — Integrity Validator + End-to-End Testing**
      Pre/post checksum diff module; integration testing across the full pipeline; scale-testing on 400+ page manuscripts.
- [ ] **Phase 4 — UI + Packaging**
      Desktop drag-and-drop interface; before/after preview; offline executable packaging.

Progress is tracked via commits on this repo. A working prototype and demo video will be added ahead of the final presentation (19th September).

## Why This Approach

- **Structure-aware, not OCR-based** — uses the `.docx` format's own machine-readable metadata instead of visual/image-based guessing
- **Explainable** — every classification decision traces to a specific, auditable feature, unlike black-box GenAI outputs
- **Provably safe** — the Integrity Validator doesn't just claim zero content change, it mathematically verifies it
- **Fully offline** — no network calls, no cloud AI, no data privacy risk for unpublished manuscripts

## License

MIT LICENSE
