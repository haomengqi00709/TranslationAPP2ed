"""
RunPod Serverless Handler

This handler processes PowerPoint translation jobs on RunPod serverless infrastructure.
It receives input via HTTP, translates the PowerPoint, and returns the download URL.
"""

import runpod
import os
import tempfile
import base64
import json
from pathlib import Path
import logging
import torch

# Force CUDA device (RunPod uses NVIDIA GPUs)
# IMPORTANT: Must be set BEFORE importing pipeline and other modules
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Disable MPS (Apple Silicon) - not available on RunPod
if hasattr(torch.backends, 'mps'):
    torch.backends.mps.is_available = lambda: False

# Override config for RunPod deployment
import config
config.LOCAL_DEVICE = "cuda"  # LLM should use CUDA (needs GPU for speed)
config.BERT_DEVICE = "cpu"    # BERT on CPU (to save GPU memory for LLM)

from pipeline import TranslationPipeline
from glossary import TerminologyGlossary

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"PyTorch version: {torch.__version__}")
logger.info(f"CUDA available: {torch.cuda.is_available()}")
logger.info(f"CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")

# Load glossary once at container startup (faster subsequent runs)
glossary = None
if Path("glossary.json").exists():
    try:
        glossary = TerminologyGlossary()
        glossary.load_from_json("glossary.json")
        glossary.compile()
        logger.info(f"Loaded glossary with {len(glossary)} entries")
    except Exception as e:
        logger.warning(f"Failed to load glossary: {e}")


def handler(job):
    """
    RunPod serverless handler function.

    Expected input format:
    {
        "input": {
            "file_base64": "<base64 encoded .pptx file>",
            "file_name": "presentation.pptx",
            "translator_type": "local",  # or "openai", "anthropic"
            "use_glossary": true,
            "source_lang": "English",  # Source language (default: "English")
            "target_lang": "French",   # Target language (default: "French")
            "context": "Optional custom terminology instructions"
        }
    }

    Returns:
    {
        "output": {
            "file_base64": "<base64 encoded translated .pptx>",
            "file_name": "presentation_translated.pptx",
            "stats": {...}
        }
    }
    """

    job_input = job["input"]

    try:
        # Extract parameters
        file_base64 = job_input.get("file_base64")
        file_name = job_input.get("file_name", "input.pptx")
        translator_type = job_input.get("translator_type", "local")
        use_glossary = job_input.get("use_glossary", True)
        source_lang = job_input.get("source_lang", "English")
        target_lang = job_input.get("target_lang", "French")
        context = job_input.get("context")

        if not file_base64:
            return {"error": "Missing 'file_base64' in input"}

        logger.info(f"Processing file: {file_name}")
        logger.info(f"Translator: {translator_type}, Use glossary: {use_glossary}")

        # Create temp directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Decode input file
            input_path = temp_path / file_name
            file_bytes = base64.b64decode(file_base64)
            with open(input_path, "wb") as f:
                f.write(file_bytes)

            logger.info(f"Input file saved: {input_path} ({len(file_bytes)} bytes)")

            # Prepare output path
            output_name = Path(file_name).stem + "_translated.pptx"
            output_path = temp_path / output_name

            # Initialize pipeline
            pipeline = TranslationPipeline(
                translator_type=translator_type,
                glossary=glossary if use_glossary else None
            )

            # Run translation
            logger.info(f"Starting translation pipeline: {source_lang} → {target_lang}...")
            stats = pipeline.run(
                input_pptx=str(input_path),
                output_pptx=str(output_path),
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
                keep_intermediate=False  # Save space
            )

            logger.info("Translation complete!")

            # Read translated file
            with open(output_path, "rb") as f:
                output_bytes = f.read()

            output_base64 = base64.b64encode(output_bytes).decode('utf-8')

            logger.info(f"Output file: {output_path} ({len(output_bytes)} bytes)")

            return {
                "file_base64": output_base64,
                "file_name": output_name,
                "stats": stats,
                "input_size_bytes": len(file_bytes),
                "output_size_bytes": len(output_bytes)
            }

    except Exception as e:
        logger.error(f"Translation failed: {e}", exc_info=True)
        return {"error": str(e)}


# Start the RunPod serverless worker
if __name__ == "__main__":
    logger.info("Starting RunPod serverless worker...")
    runpod.serverless.start({"handler": handler})
