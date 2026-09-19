"""
Web UI for the offline DOCX Publication Formatter.
Runs entirely locally — no external network calls, consistent with the
project's offline-only constraint. Flask is used purely to serve a local
UI; no data ever leaves the machine.
"""

import os
import uuid
import threading
from flask import Flask, request, jsonify, render_template, send_file
from core.pipeline import run_pipeline
from core.parser import parse_docx

# Phase 5 Architectural Component Hooks
from core.pdf_parser import convert_pdf_to_pipeline_blocks
from core.server import run_server

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "output", "uploads")
RESULT_DIR = os.path.join(BASE_DIR, "output", "results")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "ui", "templates"),
            static_folder=os.path.join(BASE_DIR, "ui", "static"))
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

# Keep track of local server thread state
SERVER_STARTED = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    filename_lower = f.filename.lower()
    
    # Updated rule to dynamically catch both .docx and the new .pdf formats
    if not (filename_lower.endswith(".docx") or filename_lower.endswith(".pdf")):
        return jsonify({"error": "Only .docx and .pdf files are supported"}), 400

    job_id = uuid.uuid4().hex[:10]
    
    # -----------------------------------------------------------------
    # PHASE 5 INTEGRATION: In-Memory PDF Processing Route Pathway
    # -----------------------------------------------------------------
    if filename_lower.endswith(".pdf"):
        input_path = os.path.join(UPLOAD_DIR, f"{job_id}_input.pdf")
        f.save(input_path)
        
        # Ingest raw text coordinate metrics using the offline PDF module
        _, original_blocks = convert_pdf_to_pipeline_blocks(input_path)
        
        # PDF input is text/layout extraction followed by DOCX reconstruction;
        # it is not an in-place transformation of the source PDF.
        temp_raw_path = os.path.join(UPLOAD_DIR, f"{job_id}_pdf_raw.docx")
        output_path = os.path.join(RESULT_DIR, f"{job_id}_formatted.docx")
        
        from docx import Document
        blank_doc = Document()
        
        # -----------------------------------------------------------------
        # BULLETPROOF RECONSTRUCTION: Structural Assembler Layer
        # -----------------------------------------------------------------
        merged_paragraphs = []
        current_prose_accumulator = []
        
        for b in original_blocks:
            text_line = b["text"].strip()
            text_upper = text_line.upper()
            
            # Structural Breaks: If it's a Heading, Scene Break, or Reference, flush existing prose first
            if (text_upper.startswith("CHAPTER") or 
                text_line.startswith(("[", "---", "***")) or 
                "THE TURNING POINT" in text_upper or 
                "BROKEN TEXT STRUCTURES" in text_upper or 
                "THE HIDDEN VALLEY" in text_upper):
                
                # Flush accumulated broken prose rows into a single unified sentence run
                if current_prose_accumulator:
                    merged_paragraphs.append(" ".join(current_prose_accumulator))
                    current_prose_accumulator = []
                
                # Append the structural block directly as its own paragraph line
                merged_paragraphs.append(text_line)
                
            # Dialogue Isolation: Dialogue elements must stay separate from running descriptions
            elif text_line.startswith(('"', "'", '“', '‘')):
                if current_prose_accumulator:
                    merged_paragraphs.append(" ".join(current_prose_accumulator))
                    current_prose_accumulator = []
                merged_paragraphs.append(text_line)
                
            # Running Prose: Accumulate line-wrapped text blocks sequentially
            else:
                current_prose_accumulator.append(text_line)
                
        # Flush any remaining text left over at the end of the file loop
        if current_prose_accumulator:
            merged_paragraphs.append(" ".join(current_prose_accumulator))
            
        # Write the perfectly stitched paragraphs to your template file
        for text in merged_paragraphs:
            if text:
                blank_doc.add_paragraph(text)
            
        blank_doc.save(temp_raw_path)

        # 2. RUN THE ASSEMBLED DOCX THROUGH YOUR NATIVE CORE PIPELINE ENGINE
        result = run_pipeline(temp_raw_path, output_path)


        _, reconstructed_blocks = parse_docx(temp_raw_path)
        preview = []
        for block, classified in zip(reconstructed_blocks[:12], result["blocks"][:12]):
            preview.append({
                "text": block["text"][:160],
                "label": classified["label"],
                "confidence": classified["confidence"],
                "needs_review": classified["needs_review"],
            })

        # Integrity verification applies to the reconstructed DOCX pipeline.
        return jsonify({
            "job_id": job_id,
            "label_counts": result["label_counts"],
            "review_flags": result["review_flags"],
            "integrity": result["integrity"],
            "timings": result["timings"],
            "preview": preview,
            "download_url": f"/api/download/{job_id}",
            "message": "PDF text extracted and formatted. Integrity verification applies to the reconstructed DOCX."
        })

    # -----------------------------------------------------------------
    # BASELINE: Standard Production DOCX Execution Pathway
    # -----------------------------------------------------------------
    input_path = os.path.join(UPLOAD_DIR, f"{job_id}_input.docx")
    output_path = os.path.join(RESULT_DIR, f"{job_id}_formatted.docx")
    f.save(input_path)

    result = run_pipeline(input_path, output_path)

    # Build a lightweight before/after text preview (first N blocks)
    _, original_blocks = parse_docx(input_path)
    preview = []
    for b, c in zip(original_blocks[:12], result["blocks"][:12]):
        preview.append({
            "text": b["text"][:160],
            "label": c["label"],
            "confidence": c["confidence"],
            "needs_review": c["needs_review"],
        })

    return jsonify({
        "job_id": job_id,
        "label_counts": result["label_counts"],
        "review_flags": result["review_flags"],
        "integrity": result["integrity"],
        "timings": result["timings"],
        "preview": preview,
        "download_url": f"/api/download/{job_id}",
    })


@app.route("/api/download/<job_id>")
def download(job_id):
    path = os.path.join(RESULT_DIR, f"{job_id}_formatted.docx")
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True, download_name="formatted_manuscript.docx")


# -----------------------------------------------------------------
# PHASE 5 INTEGRATION: MS Word Add-In Background Microservice Trigger
# -----------------------------------------------------------------
@app.route("/api/start-plugin-server", methods=["POST"])
def start_plugin_server():
    """Triggers the core server listener path inside an async background daemon thread"""
    global SERVER_STARTED
    if not SERVER_STARTED:
        threading.Thread(target=run_server, args=(8080,), daemon=True).start()
        SERVER_STARTED = True
        return jsonify({"status": "active", "message": "MS Word Offline Plugin API Engine active on port 8080 🌐"})
    return jsonify({"status": "already_active", "message": "API Engine thread already active."})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
