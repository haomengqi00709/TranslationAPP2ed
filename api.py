"""
FastAPI Translation Service

Provides REST API endpoints for PowerPoint translation with BERT alignment.
Supports background job processing with Redis queue.
"""

import os
import uuid
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (override=True to ensure .env values take precedence)
load_dotenv(override=True)

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import pipeline components
# Pipeline needs torch - only available when running with full ML stack
# (Not needed on Railway proxy mode - only forwards to RunPod)
try:
    from pipeline import TranslationPipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    # Pipeline not available (missing torch/transformers)
    # This is expected on Railway - it only runs RunPod proxy mode
    TranslationPipeline = None
    PIPELINE_AVAILABLE = False

from glossary import TerminologyGlossary
import config

# Import Ultimate Translation components (from layout_solution)
import sys
layout_solution_path = str(Path(__file__).parent / "layout_solution")
if layout_solution_path not in sys.path:
    sys.path.insert(0, layout_solution_path)

# Import directly from layout_solution folder (without package prefix since we added to sys.path)
from extract_ppt_v2 import extract_presentation
from export_slides_as_images import export_ppt_with_pdf2image
from translate_ai_v5 import restructure_all_slides_v5, flatten_to_slides, load_glossary as load_ultimate_glossary
from render_html_v5 import render_html_v5
from export_pdf import export_html_to_pdf

# Import RunPod client
import runpod
import base64

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PowerPoint Translation API",
    description="Translate PowerPoint presentations with formatting preservation",
    version="1.0.0"
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job storage with persistence
JOBS_FILE = Path("jobs.json")

def load_jobs():
    """Load jobs from disk."""
    if JOBS_FILE.exists():
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load jobs from disk: {e}")
            return {}
    return {}

def save_jobs():
    """Save jobs to disk."""
    try:
        with open(JOBS_FILE, 'w') as f:
            json.dump(jobs, f)
    except Exception as e:
        logger.error(f"Failed to save jobs to disk: {e}")

# Load existing jobs from disk on startup
jobs = load_jobs()
logger.info(f"Loaded {len(jobs)} jobs from disk")

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# File retention settings (for Railway ephemeral storage)
FILE_RETENTION_HOURS = 24  # Delete files older than 24 hours


def cleanup_old_files():
    """
    Clean up old uploaded and output files to prevent disk space issues.
    Useful for Railway deployment with ephemeral storage.
    """
    import time

    current_time = time.time()
    retention_seconds = FILE_RETENTION_HOURS * 3600
    deleted_count = 0

    # Clean upload directory
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > retention_seconds:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old upload: {file_path.name} (age: {file_age/3600:.1f}h)")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")

    # Clean output directory
    for file_path in OUTPUT_DIR.glob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > retention_seconds:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old output: {file_path.name} (age: {file_age/3600:.1f}h)")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleanup complete: deleted {deleted_count} old files")

    return deleted_count

# RunPod Configuration (set via environment variables or directly)
USE_RUNPOD = os.getenv("USE_RUNPOD", "false").lower() == "true"
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", "")

if USE_RUNPOD:
    if not RUNPOD_ENDPOINT_ID or not RUNPOD_API_KEY:
        logger.warning("USE_RUNPOD=true but RUNPOD_ENDPOINT_ID or RUNPOD_API_KEY not set!")
        logger.warning("Falling back to local execution")
        USE_RUNPOD = False
    else:
        runpod.api_key = RUNPOD_API_KEY
        logger.info(f"RunPod mode enabled - endpoint: {RUNPOD_ENDPOINT_ID}")

# Load glossary if available
glossary = None
if Path("glossary.json").exists():
    try:
        glossary = TerminologyGlossary()
        glossary.load_from_json("glossary.json")
        glossary.compile()
        logger.info(f"Loaded glossary with {len(glossary)} entries")
    except Exception as e:
        logger.warning(f"Failed to load glossary: {e}")


# ==============================================================================
# Startup Event
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Run cleanup on startup to remove old files from previous sessions."""
    logger.info("Running startup cleanup...")
    cleanup_old_files()


# ==============================================================================
# Pydantic Models
# ==============================================================================

class TranslationRequest(BaseModel):
    """Translation request parameters."""
    translator_type: str = "local"  # "local", "openai", or "anthropic"
    source_language: str = "English"
    target_language: str = "French"
    use_glossary: bool = True
    context: Optional[str] = None


class JobStatus(BaseModel):
    """Job status response."""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    created_at: str
    updated_at: str
    download_url: Optional[str] = None
    html_download_url: Optional[str] = None  # For Ultimate Translation
    pdf_download_url: Optional[str] = None   # For Ultimate Translation
    error: Optional[str] = None


# ==============================================================================
# Background Task Functions
# ==============================================================================

def process_translation(
    job_id: str,
    input_path: Path,
    output_path: Path,
    translator_type: str,
    use_glossary: bool,
    source_lang: str,
    target_lang: str,
    context: Optional[str]
):
    """Background task to process translation."""

    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        if USE_RUNPOD:
            # ==================================================================
            # RunPod Mode: Forward to serverless endpoint
            # ==================================================================
            jobs[job_id]["message"] = "Sending to RunPod..."
            logger.info(f"[{job_id}] Forwarding to RunPod endpoint: {RUNPOD_ENDPOINT_ID}")

            # Read and encode input file
            with open(input_path, "rb") as f:
                file_bytes = f.read()
                file_base64 = base64.b64encode(file_bytes).decode('utf-8')

            # Prepare RunPod request
            endpoint = runpod.Endpoint(RUNPOD_ENDPOINT_ID)
            job_input = {
                "file_base64": file_base64,
                "file_name": input_path.name,
                "translator_type": translator_type,
                "use_glossary": use_glossary,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
            if context:
                job_input["context"] = context

            jobs[job_id]["progress"] = 20
            jobs[job_id]["message"] = "Translating on RunPod (this may take several minutes)..."

            # Start RunPod job
            run_request = endpoint.run(job_input)

            # Poll for completion
            import time
            max_wait = 1200  # 20 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                # Check if job was cancelled
                if jobs[job_id].get("status") == "cancelled":
                    logger.info(f"[{job_id}] Job cancelled by user")
                    jobs[job_id]["message"] = "Translation cancelled by user"
                    jobs[job_id]["updated_at"] = datetime.now().isoformat()
                    return

                # Try to get status with retry logic
                try:
                    status = run_request.status()
                except Exception as status_error:
                    logger.warning(f"[{job_id}] Error checking RunPod status (will retry): {status_error}")
                    jobs[job_id]["message"] = "Connecting to RunPod (retrying)..."
                    time.sleep(5)
                    continue

                elapsed = int(time.time() - start_time)

                # Handle queue status
                if status == "IN_QUEUE":
                    jobs[job_id]["progress"] = 15
                    jobs[job_id]["message"] = "⏳ Your task is in queue... Waiting for available GPU"
                    jobs[job_id]["updated_at"] = datetime.now().isoformat()
                    logger.info(f"[{job_id}] Job in RunPod queue ({elapsed}s elapsed)")
                    time.sleep(5)
                    continue

                elif status == "IN_PROGRESS":
                    # Job is running on GPU - use detailed progress milestones
                    pass  # Will be handled below

                elif status == "COMPLETED":
                    # Get output with retry
                    try:
                        result = run_request.output()
                    except Exception as output_error:
                        logger.warning(f"[{job_id}] Error getting RunPod output (will retry): {output_error}")
                        time.sleep(5)
                        continue

                    # Decode and save result
                    if "file_base64" in result:
                        output_bytes = base64.b64decode(result["file_base64"])
                        with open(output_path, "wb") as f:
                            f.write(output_bytes)

                        # Store translation pairs if available
                        translation_pairs = result.get("stats", {}).get("translation_pairs", [])

                        jobs[job_id]["status"] = "completed"
                        jobs[job_id]["progress"] = 100
                        jobs[job_id]["message"] = f"Translation completed in {elapsed}s"
                        jobs[job_id]["download_url"] = f"/api/download/{job_id}"
                        jobs[job_id]["translation_pairs"] = translation_pairs
                        jobs[job_id]["updated_at"] = datetime.now().isoformat()
                        save_jobs()  # Persist completion to disk

                        logger.info(f"[{job_id}] RunPod translation completed: {output_path}, {len(translation_pairs)} translation pairs")
                        return
                    else:
                        raise Exception("No file_base64 in RunPod response")

                elif status == "FAILED":
                    # Try to get detailed error from RunPod output
                    try:
                        result = run_request.output()
                        error_msg = result.get("error", str(result)) if result else "Unknown error"
                        logger.error(f"[{job_id}] RunPod job failed with result: {result}")
                    except Exception as e:
                        error_msg = f"Failed to get error details: {str(e)}"
                        logger.error(f"[{job_id}] Could not retrieve RunPod error: {e}")

                    raise Exception(f"RunPod job failed: {error_msg}")

                # If IN_PROGRESS, update with meaningful milestones
                if status == "IN_PROGRESS":
                    if elapsed < 30:
                        progress = 25
                        message = "🚀 Starting translation engine..."
                    elif elapsed < 60:
                        progress = 35
                        message = "📄 Processing slides..."
                    elif elapsed < 120:
                        progress = 50
                        message = "✍️ Translating content..."
                    elif elapsed < 180:
                        progress = 65
                        message = "🎨 Applying formatting..."
                    elif elapsed < 240:
                        progress = 80
                        message = "🔍 Quality check..."
                    else:
                        progress = min(90, 20 + int((elapsed / max_wait) * 70))
                        message = f"⏳ Finalizing... ({elapsed}s elapsed)"

                    jobs[job_id]["progress"] = progress
                    jobs[job_id]["message"] = message
                    jobs[job_id]["updated_at"] = datetime.now().isoformat()

                time.sleep(5)  # Check every 5 seconds

            raise Exception(f"RunPod translation timed out after {max_wait}s")

        else:
            # ==================================================================
            # Local Mode: Run pipeline locally
            # ==================================================================
            if not PIPELINE_AVAILABLE:
                raise RuntimeError(
                    "Pipeline not available (missing ML dependencies). "
                    "Either set USE_RUNPOD=true or install full dependencies: pip install -r requirements-full.txt"
                )

            jobs[job_id]["message"] = "Initializing pipeline..."

            # Initialize pipeline
            pipeline = TranslationPipeline(
                translator_type=translator_type,
                glossary=glossary if use_glossary else None
            )

            jobs[job_id]["progress"] = 20
            jobs[job_id]["message"] = "Extracting content..."

            # Run translation
            logger.info(f"[{job_id}] Starting local translation: {input_path}")

            pipeline.run(
                input_pptx=str(input_path),
                output_pptx=str(output_path),
                source_lang=source_lang,
                target_lang=target_lang,
                context=context
            )

            # Success
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Translation completed successfully"
            jobs[job_id]["download_url"] = f"/api/download/{job_id}"
            jobs[job_id]["updated_at"] = datetime.now().isoformat()
            save_jobs()  # Persist completion to disk

            logger.info(f"[{job_id}] Local translation completed: {output_path}")

    except Exception as e:
        # Failure
        logger.error(f"[{job_id}] Translation failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["progress"] = 0
        jobs[job_id]["message"] = "Translation failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = datetime.now().isoformat()
        save_jobs()  # Persist failure to disk


def process_ultimate_translation(
    job_id: str,
    input_path: Path,
    output_html_path: Path,
    output_pdf_path: Path,
    source_lang: str,
    target_lang: str,
    use_glossary: bool
):
    """Background task to process Ultimate Translation (AI restructured HTML + PDF)."""

    try:
        # LOCKED: Always use English → French (ignore source_lang/target_lang params)
        source_lang = "English"
        target_lang = "French"

        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 5
        jobs[job_id]["message"] = "Extracting slides..."
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Get Gemini API key
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise Exception("GEMINI_API_KEY not found in environment")

        # Create temp directories
        temp_dir = Path("temp") / job_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        slides_images_dir = temp_dir / "slides_images"
        slides_images_dir.mkdir(exist_ok=True)

        # Step 1: Extract slides
        logger.info(f"[{job_id}] Extracting slides from {input_path}")
        extracted_file = temp_dir / "extracted_slides.json"
        slides_data = extract_presentation(str(input_path))

        jobs[job_id]["progress"] = 15
        jobs[job_id]["message"] = "Exporting slide images..."
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Step 2: Export slides as images for vision analysis
        logger.info(f"[{job_id}] Exporting slides as images")
        export_ppt_with_pdf2image(str(input_path), str(slides_images_dir))

        jobs[job_id]["progress"] = 25
        jobs[job_id]["message"] = "Loading glossary..."
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Step 3: Load glossary
        ultimate_glossary = load_ultimate_glossary() if use_glossary else {}

        jobs[job_id]["progress"] = 30
        jobs[job_id]["message"] = f"AI restructuring content ({source_lang} → {target_lang})..."
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Step 4: AI restructuring with translation
        # Note: layout_solution is hardcoded to English→French, doesn't need lang params
        logger.info(f"[{job_id}] AI restructuring slides ({source_lang} → {target_lang})")
        restructured_data = restructure_all_slides_v5(
            slides_data,
            ultimate_glossary,
            gemini_api_key,
            slides_images_dir
        )

        jobs[job_id]["progress"] = 70
        jobs[job_id]["message"] = "Flattening slides..."
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Step 5: Flatten to simple slide list
        flattened_slides = flatten_to_slides(restructured_data)

        # DEBUG: Save intermediate JSON for debugging
        debug_json_path = OUTPUT_DIR / f"{job_id}_debug_slides.json"
        with open(debug_json_path, 'w', encoding='utf-8') as f:
            json.dump(flattened_slides, f, ensure_ascii=False, indent=2)
        logger.info(f"[{job_id}] DEBUG: Saved {len(flattened_slides)} slides to {debug_json_path}")

        jobs[job_id]["progress"] = 75
        jobs[job_id]["message"] = "Rendering HTML..."
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Step 6: Render HTML (layout_solution has built-in template)
        logger.info(f"[{job_id}] Rendering HTML")
        render_html_v5(
            slides_data=flattened_slides,
            template_path=str(Path(__file__).parent / "layout_solution" / "template_v4.html"),
            output_path=str(output_html_path)
        )

        jobs[job_id]["progress"] = 85
        jobs[job_id]["message"] = "Generating PDF..."
        jobs[job_id]["updated_at"] = datetime.now().isoformat()

        # Step 7: Export to PDF
        logger.info(f"[{job_id}] Generating PDF")
        export_html_to_pdf(str(output_html_path), str(output_pdf_path))

        # Success
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Ultimate Translation completed"
        jobs[job_id]["html_download_url"] = f"/api/download/ultimate/html/{job_id}"
        jobs[job_id]["pdf_download_url"] = f"/api/download/ultimate/pdf/{job_id}"
        jobs[job_id]["updated_at"] = datetime.now().isoformat()
        save_jobs()

        logger.info(f"[{job_id}] Ultimate Translation completed: HTML={output_html_path}, PDF={output_pdf_path}")

    except Exception as e:
        # Failure
        logger.error(f"[{job_id}] Ultimate Translation failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["progress"] = 0
        jobs[job_id]["message"] = "Ultimate Translation failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = datetime.now().isoformat()
        save_jobs()


# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - Serve web UI."""
    html_file = Path("frontend/index.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)
    else:
        # Fallback to JSON if no frontend
        return JSONResponse({
            "name": "PowerPoint Translation API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "translate": "POST /api/translate",
                "status": "GET /api/status/{job_id}",
                "download": "GET /api/download/{job_id}",
                "glossary": "GET /api/glossary"
            }
        })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "glossary_loaded": glossary is not None,
        "glossary_entries": len(glossary) if glossary else 0
    }


@app.post("/api/translate")
async def translate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    translator_type: str = "local",
    use_glossary: bool = True,
    source_lang: str = "English",
    target_lang: str = "French",
    context: Optional[str] = None
):
    """
    Translate a PowerPoint presentation.

    Parameters:
    - file: PowerPoint file (.pptx)
    - translator_type: "local", "openai", or "anthropic"
    - use_glossary: Whether to use terminology glossary
    - source_lang: Source language (default: "English")
    - target_lang: Target language (default: "French")
    - context: Optional context/instructions for translation

    Returns:
    - job_id: Unique job identifier for tracking
    """

    # Validate file
    if not file.filename.endswith('.pptx'):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Cleanup old files (run periodically when new uploads arrive)
    try:
        cleanup_old_files()
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")

    # Save uploaded file
    input_path = UPLOAD_DIR / f"{job_id}_input.pptx"
    output_path = OUTPUT_DIR / f"{job_id}_output.pptx"

    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)

    logger.info(f"[{job_id}] Received file: {file.filename} ({len(content)} bytes)")

    # Create job record
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Job created, waiting to start...",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "filename": file.filename,
        "translator_type": translator_type,
        "use_glossary": use_glossary,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "download_url": None,
        "error": None
    }
    save_jobs()  # Persist job to disk

    # Start background processing
    background_tasks.add_task(
        process_translation,
        job_id=job_id,
        input_path=input_path,
        output_path=output_path,
        translator_type=translator_type,
        use_glossary=use_glossary,
        source_lang=source_lang,
        target_lang=target_lang,
        context=context
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Translation job created successfully",
        "status_url": f"/api/status/{job_id}"
    }


@app.post("/api/translate/ultimate")
async def translate_ultimate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_glossary: bool = True,
    source_lang: str = "English",
    target_lang: str = "French"
):
    """
    Ultimate Translation: AI-powered content restructuring with HTML + PDF output.

    This endpoint uses Gemini Vision AI to analyze charts, restructure content,
    and generate magazine-style HTML and PDF outputs.

    Parameters:
    - file: PowerPoint file (.pptx)
    - use_glossary: Whether to use terminology glossary
    - source_lang: Source language (default: "English")
    - target_lang: Target language (default: "French")

    Returns:
    - job_id: Unique job identifier for tracking
    - status_url: URL to check job status
    """

    # Validate file
    if not file.filename.endswith('.pptx'):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported")

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Cleanup old files (run periodically when new uploads arrive)
    try:
        cleanup_old_files()
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")

    # Save uploaded file
    input_path = UPLOAD_DIR / f"{job_id}_input.pptx"
    output_html_path = OUTPUT_DIR / f"{job_id}_ultimate.html"
    output_pdf_path = OUTPUT_DIR / f"{job_id}_ultimate.pdf"

    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)

    logger.info(f"[{job_id}] Ultimate Translation received: {file.filename} ({len(content)} bytes)")

    # Create job record
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "message": "Ultimate Translation job created, waiting to start...",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "filename": file.filename,
        "translation_mode": "ultimate",
        "use_glossary": use_glossary,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "input_path": str(input_path),
        "output_html_path": str(output_html_path),
        "output_pdf_path": str(output_pdf_path),
        "html_download_url": None,
        "pdf_download_url": None,
        "error": None
    }
    save_jobs()

    # Start background processing
    background_tasks.add_task(
        process_ultimate_translation,
        job_id=job_id,
        input_path=input_path,
        output_html_path=output_html_path,
        output_pdf_path=output_pdf_path,
        source_lang=source_lang,
        target_lang=target_lang,
        use_glossary=use_glossary
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Ultimate Translation job created successfully",
        "status_url": f"/api/status/{job_id}"
    }


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """
    Get status of a translation job.

    Returns:
    - Job status, progress, and download URL if completed
    """

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        download_url=job.get("download_url"),
        html_download_url=job.get("html_download_url"),
        pdf_download_url=job.get("pdf_download_url"),
        error=job.get("error")
    )


@app.post("/api/cancel/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running translation job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # Only cancel if job is still processing
    if job["status"] in ["pending", "processing"]:
        jobs[job_id]["status"] = "cancelled"
        jobs[job_id]["progress"] = 0
        jobs[job_id]["message"] = "Translation cancelled by user"
        jobs[job_id]["updated_at"] = datetime.now().isoformat()
        save_jobs()  # Persist cancellation to disk
        logger.info(f"Job {job_id} cancelled by user")
        return {"status": "cancelled", "message": "Job cancelled successfully"}
    else:
        return {"status": job["status"], "message": f"Job already {job['status']}"}


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    """
    Download translated PowerPoint file.

    Returns:
    - Translated .pptx file
    """

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet (status: {job['status']})"
        )

    output_path = Path(job["output_path"])

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    # Extract original filename
    original_name = job.get("filename", "presentation.pptx")
    base_name = Path(original_name).stem
    download_name = f"{base_name}_translated.pptx"

    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=download_name
    )


@app.get("/api/download/ultimate/html/{job_id}")
async def download_ultimate_html(job_id: str):
    """
    Download Ultimate Translation HTML file.

    Returns:
    - Translated HTML file
    """

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet (status: {job['status']})"
        )

    output_path = Path(job["output_html_path"])

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="HTML file not found")

    # Extract original filename
    original_name = job.get("filename", "presentation.pptx")
    base_name = Path(original_name).stem
    download_name = f"{base_name}_ultimate.html"

    return FileResponse(
        path=output_path,
        media_type="text/html",
        filename=download_name
    )


@app.get("/api/download/ultimate/pdf/{job_id}")
async def download_ultimate_pdf(job_id: str):
    """
    Download Ultimate Translation PDF file.

    Returns:
    - Translated PDF file
    """

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet (status: {job['status']})"
        )

    output_path = Path(job["output_pdf_path"])

    if not output_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Extract original filename
    original_name = job.get("filename", "presentation.pptx")
    base_name = Path(original_name).stem
    download_name = f"{base_name}_ultimate.pdf"

    return FileResponse(
        path=output_path,
        media_type="application/pdf",
        filename=download_name
    )


@app.get("/api/glossary")
async def get_glossary():
    """
    Get current glossary entries.

    Returns:
    - List of glossary terms
    """

    if not glossary:
        return {"entries": [], "count": 0}

    entries = [
        {
            "source": entry.source,
            "target": entry.target,
            "priority": entry.priority,
            "case_sensitive": entry.case_sensitive,
            "context": entry.context,
            "notes": entry.notes
        }
        for entry in glossary.entries
    ]

    return {
        "entries": entries,
        "count": len(entries)
    }


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its associated files.

    Returns:
    - Success message
    """

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # Delete files
    input_path = Path(job["input_path"])
    output_path = Path(job["output_path"])

    if input_path.exists():
        input_path.unlink()
    if output_path.exists():
        output_path.unlink()

    # Delete job record
    del jobs[job_id]

    logger.info(f"[{job_id}] Job deleted")

    return {"message": "Job deleted successfully"}


# Note: Static HTML is served directly from the root endpoint above
# No need for StaticFiles mount since we only have a single index.html


if __name__ == "__main__":
    import uvicorn

    # Run server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
