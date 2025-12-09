#!/usr/bin/env python3
"""
API Wrapper for PowerPoint to PDF Pipeline
Wraps all 5 stages into a single function for easy integration.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, Callable, Optional
from dotenv import load_dotenv

# Import all pipeline stages
from extract_ppt_v2 import extract_presentation
from export_slides_as_images import export_ppt_to_images
from translate_ai_v5 import restructure_all_slides_v5, flatten_to_slides, load_glossary
from render_html_v5 import render_html_v5
from export_pdf import export_html_to_pdf


class PipelineProgress:
    """Track pipeline progress for frontend updates."""
    def __init__(self):
        self.current_stage = 0
        self.total_stages = 5
        self.status = "idle"
        self.message = ""
        self.error = None

    def to_dict(self):
        return {
            "current_stage": self.current_stage,
            "total_stages": self.total_stages,
            "progress_percent": int((self.current_stage / self.total_stages) * 100),
            "status": self.status,
            "message": self.message,
            "error": self.error
        }


def ppt_to_pdf_pipeline(
    ppt_path: str,
    output_dir: str = "output",
    progress_callback: Optional[Callable[[PipelineProgress], None]] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    Complete pipeline: PowerPoint → French PDF with AI restructuring and chart vision.

    Args:
        ppt_path: Path to input PowerPoint file
        output_dir: Directory for all outputs (default: "output")
        progress_callback: Optional callback function for progress updates
        api_key: Gemini API key (if not in .env)

    Returns:
        dict with:
        {
            "success": True/False,
            "pdf_path": "path/to/output.pdf",
            "html_path": "path/to/output.html",
            "stats": {...},
            "error": "error message if failed"
        }
    """
    progress = PipelineProgress()

    def update_progress(stage: int, status: str, message: str):
        progress.current_stage = stage
        progress.status = status
        progress.message = message
        if progress_callback:
            progress_callback(progress)

    try:
        # Load environment variables
        load_dotenv()
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env or provided")

        # Setup paths
        ppt_path = Path(ppt_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        extracted_json = output_dir / "extracted_slides_v2.json"
        images_dir = output_dir / "slides_images"
        translated_json = output_dir / "translated_slides_v5.json"
        html_output = output_dir / "output_v5.html"
        pdf_output = output_dir / "output_v5.pdf"

        # ========== STAGE 1: Extract PPT Content ==========
        update_progress(1, "running", "Extracting content from PowerPoint...")

        slides_data = extract_presentation(str(ppt_path))

        with open(extracted_json, 'w', encoding='utf-8') as f:
            json.dump(slides_data, f, ensure_ascii=False, indent=2)

        update_progress(1, "complete", f"Extracted {len(slides_data)} slides")

        # ========== STAGE 2: Export Slide Images ==========
        update_progress(2, "running", "Generating slide images for chart analysis...")

        export_ppt_to_images(
            ppt_path=str(ppt_path),
            output_dir=str(images_dir)
        )

        update_progress(2, "complete", f"Exported slide images to {images_dir.name}")

        # ========== STAGE 3: AI Translation + Vision Analysis ==========
        update_progress(3, "running", "AI analyzing content and extracting charts...")

        glossary = load_glossary()

        restructured_data = restructure_all_slides_v5(
            slides_data=slides_data,
            glossary=glossary,
            api_key=api_key,
            image_dir=images_dir
        )

        flattened_slides = flatten_to_slides(restructured_data)

        with open(translated_json, 'w', encoding='utf-8') as f:
            json.dump(flattened_slides, f, ensure_ascii=False, indent=2)

        # Count chart slides
        chart_slides = len([s for s in flattened_slides
                           if s.get('layout_type') in ['bar_chart', 'pie_chart', 'column_chart', 'line_chart']])

        update_progress(3, "complete",
                       f"Translated {len(flattened_slides)} slides, {chart_slides} charts recreated")

        # ========== STAGE 4: Render HTML ==========
        update_progress(4, "running", "Rendering HTML with Chart.js...")

        render_html_v5(
            slides_data=flattened_slides,
            output_path=str(html_output)
        )

        update_progress(4, "complete", f"HTML generated: {html_output.name}")

        # ========== STAGE 5: Export PDF ==========
        update_progress(5, "running", "Converting to PDF (rendering charts)...")

        export_html_to_pdf(
            html_path=str(html_output),
            pdf_path=str(pdf_output)
        )

        pdf_size_mb = pdf_output.stat().st_size / (1024 * 1024)

        update_progress(5, "complete", f"PDF exported: {pdf_size_mb:.2f} MB")

        # ========== SUCCESS ==========
        progress.status = "success"

        return {
            "success": True,
            "pdf_path": str(pdf_output),
            "html_path": str(html_output),
            "stats": {
                "source_slides": len(slides_data),
                "output_slides": len(flattened_slides),
                "chart_slides": chart_slides,
                "pdf_size_mb": round(pdf_size_mb, 2)
            },
            "error": None
        }

    except Exception as e:
        progress.status = "error"
        progress.error = str(e)
        if progress_callback:
            progress_callback(progress)

        return {
            "success": False,
            "pdf_path": None,
            "html_path": None,
            "stats": {},
            "error": str(e)
        }


def main():
    """Test the pipeline wrapper."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 api_wrapper.py path/to/presentation.pptx")
        sys.exit(1)

    ppt_path = sys.argv[1]

    print("🚀 Running Complete Pipeline\n")

    # Progress callback for console output
    def show_progress(progress: PipelineProgress):
        p = progress.to_dict()
        print(f"[{p['progress_percent']}%] Stage {p['current_stage']}/{p['total_stages']}: {p['message']}")

    result = ppt_to_pdf_pipeline(
        ppt_path=ppt_path,
        progress_callback=show_progress
    )

    print("\n" + "="*70)
    if result["success"]:
        print("✅ Pipeline completed successfully!")
        print(f"\n📄 PDF: {result['pdf_path']}")
        print(f"🌐 HTML: {result['html_path']}")
        print(f"\n📊 Stats:")
        for key, value in result['stats'].items():
            print(f"   {key}: {value}")
    else:
        print("❌ Pipeline failed!")
        print(f"Error: {result['error']}")
    print("="*70)


if __name__ == "__main__":
    main()
