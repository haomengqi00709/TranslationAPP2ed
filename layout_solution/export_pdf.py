#!/usr/bin/env python3
"""
Stage 4: PDF Export
Converts HTML output to high-quality PDF using Playwright (headless browser).
Ensures Chart.js charts are fully rendered before export.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def export_html_to_pdf(
    html_path: str = "output/output_v5.html",
    pdf_path: str = "output/output_v5.pdf",
    wait_for_charts: bool = True
):
    """
    Export HTML to PDF using Playwright.

    Args:
        html_path: Path to HTML file
        pdf_path: Path for output PDF
        wait_for_charts: Wait for Chart.js to finish rendering

    Returns:
        Path to generated PDF
    """
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    # Ensure output directory exists
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"📄 Converting HTML to PDF...")
    print(f"   Input:  {html_path}")
    print(f"   Output: {pdf_path}")

    with sync_playwright() as p:
        # Launch browser in headless mode with additional args for macOS stability
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-setuid-sandbox',
                '--no-first-run',
                '--no-zygote',
                '--single-process'
            ]
        )
        page = browser.new_page(
            viewport={'width': 1920, 'height': 1080}
        )

        # Load HTML file
        page.goto(f"file://{html_path}")

        if wait_for_charts:
            # Wait for Chart.js to render all charts
            print(f"   ⏳ Waiting for Chart.js to render charts...")

            try:
                # Wait for Chart.js to be loaded
                page.wait_for_function("typeof Chart !== 'undefined'", timeout=5000)

                # Wait for all canvas elements to be rendered
                page.wait_for_function(
                    """() => {
                        const canvases = document.querySelectorAll('canvas');
                        if (canvases.length === 0) return true;
                        return Array.from(canvases).every(canvas => {
                            const ctx = canvas.getContext('2d');
                            return canvas.width > 0 && canvas.height > 0;
                        });
                    }""",
                    timeout=10000
                )

                # Additional delay to ensure charts are fully painted
                page.wait_for_timeout(2000)
                print(f"   ✅ Charts rendered successfully")

            except Exception as e:
                print(f"   ⚠️  Warning: Chart rendering check failed: {e}")
                print(f"   Continuing with PDF export...")

        # Export to PDF with print-friendly settings
        page.pdf(
            path=str(pdf_path),
            format='Letter',  # 8.5" x 11" (US Letter)
            margin={
                'top': '0.5in',
                'right': '0.5in',
                'bottom': '0.5in',
                'left': '0.5in'
            },
            print_background=True,  # Include background colors/images
            prefer_css_page_size=False,  # Use our format setting
            display_header_footer=False
        )

        browser.close()

    # Check PDF was created
    if pdf_path.exists():
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ PDF generated successfully!")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Path: {pdf_path}")
        return pdf_path
    else:
        raise RuntimeError("PDF generation failed - file not created")


def main():
    """Main entry point."""

    # Default paths
    html_path = "output/output_v5.html"
    pdf_path = "output/output_v5.pdf"

    # Allow custom paths from command line
    if len(sys.argv) > 1:
        html_path = sys.argv[1]
    if len(sys.argv) > 2:
        pdf_path = sys.argv[2]

    print("🚀 PDF Export - Convert HTML to PDF\n")

    try:
        output_pdf = export_html_to_pdf(html_path, pdf_path)

        print(f"\n🌐 To view:")
        print(f"  open {output_pdf}")

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Make sure you've run the previous steps:")
        print(f"   1. python3 extract_ppt_v2.py your-file.pptx")
        print(f"   2. python3 translate_ai_v5.py")
        print(f"   3. python3 render_html_v5.py")
        print(f"   4. python3 export_pdf.py")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error during PDF export: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
