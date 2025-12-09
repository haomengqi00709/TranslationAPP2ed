#!/usr/bin/env python3
"""
Helper script to export PowerPoint slides as images.
Uses LibreOffice in headless mode for cross-platform compatibility.
"""

import subprocess
import sys
from pathlib import Path
import shutil


def check_libreoffice():
    """Check if LibreOffice is installed."""
    # Common LibreOffice paths on different systems
    possible_paths = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
        "/usr/bin/libreoffice",  # Linux
        "/usr/bin/soffice",  # Linux alternative
        "C:\\Program Files\\LibreOffice\\program\\soffice.exe",  # Windows
        "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",  # Windows 32-bit
    ]

    for path in possible_paths:
        if Path(path).exists():
            return path

    # Try to find in PATH
    libreoffice_cmd = shutil.which("libreoffice") or shutil.which("soffice")
    if libreoffice_cmd:
        return libreoffice_cmd

    return None


def export_ppt_to_images(ppt_path, output_dir="output/slides_images"):
    """
    Export PowerPoint slides as PNG images using LibreOffice.

    Args:
        ppt_path: Path to .pptx file
        output_dir: Directory to save slide images

    Returns:
        List of generated image paths
    """
    ppt_path = Path(ppt_path)
    output_dir = Path(output_dir)

    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")

    # Check for LibreOffice
    soffice_path = check_libreoffice()
    if not soffice_path:
        print("❌ LibreOffice not found!")
        print("\n📥 Please install LibreOffice:")
        print("   macOS:   brew install --cask libreoffice")
        print("   Ubuntu:  sudo apt-get install libreoffice")
        print("   Windows: Download from https://www.libreoffice.org/download/")
        sys.exit(1)

    print(f"✅ Found LibreOffice: {soffice_path}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert PPT to images using LibreOffice headless mode
    print(f"\n🖼️  Exporting slides from: {ppt_path.name}")
    print(f"   Output directory: {output_dir}")

    try:
        # LibreOffice command to export as PNG
        cmd = [
            soffice_path,
            "--headless",
            "--convert-to", "png",
            "--outdir", str(output_dir.absolute()),
            str(ppt_path.absolute())
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            print(f"❌ LibreOffice export failed:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return []

        # LibreOffice exports as single PDF or images (behavior varies)
        # For slide-by-slide export, we need a different approach
        print("⚠️  LibreOffice direct export may not work slide-by-slide")
        print("   Using alternative method: Export to PDF then convert")

        # Alternative: Export to PDF first
        pdf_path = output_dir / f"{ppt_path.stem}.pdf"
        cmd_pdf = [
            soffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir.absolute()),
            str(ppt_path.absolute())
        ]

        result = subprocess.run(cmd_pdf, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and pdf_path.exists():
            print(f"✅ Exported to PDF: {pdf_path}")
            print("\n💡 Next step: Use a PDF-to-image tool to convert each page")
            print("   Option 1: Use `pdf2image` Python library")
            print("   Option 2: Use ImageMagick: convert -density 300 input.pdf output-%03d.png")
            return [pdf_path]

    except subprocess.TimeoutExpired:
        print("❌ LibreOffice conversion timed out")
        return []
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        return []

    return []


def export_ppt_with_pdf2image(ppt_path, output_dir="output/slides_images"):
    """
    Export PPT slides using pdf2image library (requires poppler).

    This is more reliable for slide-by-slide extraction.
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("❌ pdf2image library not installed")
        print("   Install with: pip install pdf2image")
        print("   Also requires poppler:")
        print("     macOS:   brew install poppler")
        print("     Ubuntu:  sudo apt-get install poppler-utils")
        return []

    ppt_path = Path(ppt_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # First, convert PPT to PDF using LibreOffice
    print("Step 1: Converting PPT to PDF...")
    pdf_path = export_ppt_to_images(ppt_path, output_dir)

    if not pdf_path or not pdf_path[0].exists():
        return []

    pdf_file = pdf_path[0]

    # Convert PDF pages to images
    print("\nStep 2: Converting PDF pages to PNG images...")
    try:
        images = convert_from_path(
            pdf_file,
            dpi=300,  # High quality
            fmt='png'
        )

        image_paths = []
        for i, image in enumerate(images, start=1):
            image_path = output_dir / f"slide{i}.png"
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
            print(f"   ✅ Slide {i} → {image_path.name}")

        print(f"\n✅ Exported {len(image_paths)} slides as PNG images")
        return image_paths

    except Exception as e:
        print(f"❌ Error converting PDF to images: {e}")
        return []


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 export_slides_as_images.py <path_to_ppt>")
        print("Example: python3 export_slides_as_images.py slide/survey-phase1-eng-PPT.pptx")
        sys.exit(1)

    ppt_path = sys.argv[1]

    print("🎨 PowerPoint Slide Image Exporter\n")

    # Try method with pdf2image (most reliable)
    image_paths = export_ppt_with_pdf2image(ppt_path)

    if image_paths:
        print(f"\n📁 All images saved to: output/slides_images/")
        print(f"   Total: {len(image_paths)} slides")
    else:
        print("\n❌ Failed to export slides")
        print("\n💡 Manual alternative:")
        print("   1. Open PPT in PowerPoint/Keynote")
        print("   2. File → Export → Images")
        print("   3. Save to output/slides_images/ as slide1.png, slide2.png, etc.")


if __name__ == "__main__":
    main()
