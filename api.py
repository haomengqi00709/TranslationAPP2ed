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

# Job storage (in production, use Redis or database)
# For now, simple in-memory dict
jobs = {}

# Directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

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
                "use_glossary": use_glossary
            }
            if context:
                job_input["context"] = context

            jobs[job_id]["progress"] = 20
            jobs[job_id]["message"] = "Translating on RunPod (this may take several minutes)..."

            # Start RunPod job
            run_request = endpoint.run(job_input)

            # Poll for completion
            import time
            max_wait = 600  # 10 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                # Try to get status with retry logic
                try:
                    status = run_request.status()
                except Exception as status_error:
                    logger.warning(f"[{job_id}] Error checking RunPod status (will retry): {status_error}")
                    jobs[job_id]["message"] = "Connecting to RunPod (retrying)..."
                    time.sleep(5)
                    continue

                elapsed = int(time.time() - start_time)

                if status == "COMPLETED":
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

                        jobs[job_id]["status"] = "completed"
                        jobs[job_id]["progress"] = 100
                        jobs[job_id]["message"] = f"Translation completed in {elapsed}s"
                        jobs[job_id]["download_url"] = f"/api/download/{job_id}"
                        jobs[job_id]["updated_at"] = datetime.now().isoformat()

                        logger.info(f"[{job_id}] RunPod translation completed: {output_path}")
                        return
                    else:
                        raise Exception("No file_base64 in RunPod response")

                elif status == "FAILED":
                    error_msg = result.get("error", "Unknown error") if 'result' in locals() else "Job failed on RunPod"
                    raise Exception(f"RunPod job failed: {error_msg}")

                # Update progress with meaningful milestones
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
                context=context
            )

            # Success
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Translation completed successfully"
            jobs[job_id]["download_url"] = f"/api/download/{job_id}"
            jobs[job_id]["updated_at"] = datetime.now().isoformat()

            logger.info(f"[{job_id}] Local translation completed: {output_path}")

    except Exception as e:
        # Failure
        logger.error(f"[{job_id}] Translation failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["progress"] = 0
        jobs[job_id]["message"] = "Translation failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = datetime.now().isoformat()


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
    context: Optional[str] = None
):
    """
    Translate a PowerPoint presentation.

    Parameters:
    - file: PowerPoint file (.pptx)
    - translator_type: "local", "openai", or "anthropic"
    - use_glossary: Whether to use terminology glossary
    - context: Optional context/instructions for translation

    Returns:
    - job_id: Unique job identifier for tracking
    """

    # Validate file
    if not file.filename.endswith('.pptx'):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported")

    # Generate job ID
    job_id = str(uuid.uuid4())

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
        "input_path": str(input_path),
        "output_path": str(output_path),
        "download_url": None,
        "error": None
    }

    # Start background processing
    background_tasks.add_task(
        process_translation,
        job_id=job_id,
        input_path=input_path,
        output_path=output_path,
        translator_type=translator_type,
        use_glossary=use_glossary,
        context=context
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Translation job created successfully",
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
        error=job.get("error")
    )


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
