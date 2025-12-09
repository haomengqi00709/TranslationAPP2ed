#!/usr/bin/env python3
"""
Flask API Server for PowerPoint Translation Pipeline
Provides REST endpoints for frontend integration.
"""

import os
import uuid
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from api_wrapper import ppt_to_pdf_pipeline, PipelineProgress


app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
UPLOAD_FOLDER = Path("uploads")
OUTPUT_FOLDER = Path("output")
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'pptx', 'ppt'}

# In-memory job tracking (use Redis/database in production)
jobs = {}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_pipeline_async(job_id: str, ppt_path: str, output_dir: str):
    """Run pipeline in background thread."""
    def progress_callback(progress: PipelineProgress):
        jobs[job_id]["progress"] = progress.to_dict()
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

    result = ppt_to_pdf_pipeline(
        ppt_path=ppt_path,
        output_dir=output_dir,
        progress_callback=progress_callback
    )

    jobs[job_id]["status"] = "completed" if result["success"] else "failed"
    jobs[job_id]["result"] = result
    jobs[job_id]["completed_at"] = datetime.now().isoformat()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "PowerPoint to PDF Pipeline"
    })


@app.route('/api/translate/pdf', methods=['POST'])
def translate_to_pdf():
    """
    Start PPT to PDF translation pipeline.

    Request:
        - Multipart form with 'file' (PowerPoint file)

    Response:
        {
            "job_id": "uuid",
            "status": "processing",
            "message": "Pipeline started"
        }
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only .pptx files allowed"}), 400

    # Save uploaded file
    job_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    upload_path = UPLOAD_FOLDER / job_id
    upload_path.mkdir(exist_ok=True)

    ppt_path = upload_path / filename
    file.save(str(ppt_path))

    # Setup output directory for this job
    output_dir = OUTPUT_FOLDER / job_id
    output_dir.mkdir(exist_ok=True)

    # Initialize job tracking
    jobs[job_id] = {
        "job_id": job_id,
        "filename": filename,
        "status": "processing",
        "progress": {
            "current_stage": 0,
            "total_stages": 5,
            "progress_percent": 0,
            "status": "starting",
            "message": "Initializing pipeline...",
            "error": None
        },
        "result": None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "completed_at": None
    }

    # Start pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline_async,
        args=(job_id, str(ppt_path), str(output_dir))
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "processing",
        "message": "Pipeline started successfully"
    }), 202


@app.route('/api/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """
    Get job status and progress.

    Response:
        {
            "job_id": "uuid",
            "status": "processing|completed|failed",
            "progress": {...},
            "result": {...}  // Only if completed
        }
    """
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    job = jobs[job_id]
    return jsonify(job)


@app.route('/api/jobs/<job_id>/download', methods=['GET'])
def download_pdf(job_id):
    """
    Download generated PDF.

    Query params:
        - type: 'pdf' or 'html' (default: pdf)
    """
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    job = jobs[job_id]

    if job["status"] != "completed":
        return jsonify({"error": "Job not completed yet"}), 400

    if not job["result"]["success"]:
        return jsonify({"error": "Job failed", "details": job["result"]["error"]}), 400

    file_type = request.args.get('type', 'pdf')

    if file_type == 'pdf':
        file_path = job["result"]["pdf_path"]
        mimetype = 'application/pdf'
        download_name = f"{job['filename'].rsplit('.', 1)[0]}_translated.pdf"
    elif file_type == 'html':
        file_path = job["result"]["html_path"]
        mimetype = 'text/html'
        download_name = f"{job['filename'].rsplit('.', 1)[0]}_translated.html"
    else:
        return jsonify({"error": "Invalid file type"}), 400

    if not Path(file_path).exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(
        file_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_name
    )


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs (for debugging)."""
    return jsonify({
        "total": len(jobs),
        "jobs": [
            {
                "job_id": job["job_id"],
                "filename": job["filename"],
                "status": job["status"],
                "progress_percent": job["progress"]["progress_percent"],
                "created_at": job["created_at"]
            }
            for job in jobs.values()
        ]
    })


if __name__ == '__main__':
    print("="*70)
    print("🚀 PowerPoint to PDF API Server")
    print("="*70)
    print("\nEndpoints:")
    print("  POST   /api/translate/pdf         - Start translation")
    print("  GET    /api/jobs/<id>/status      - Check progress")
    print("  GET    /api/jobs/<id>/download    - Download PDF")
    print("  GET    /api/health                - Health check")
    print("\nStarting server on http://localhost:5000")
    print("="*70)
    print()

    app.run(debug=True, port=5000, threaded=True)
