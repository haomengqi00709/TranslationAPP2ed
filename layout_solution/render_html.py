#!/usr/bin/env python3
"""
Stage 3: HTML Rendering
Renders translated slides as beautiful HTML using Jinja2 templates.
"""

import json
import sys
from pathlib import Path
from jinja2 import Template


def extract_primary_color(ppt_path=None):
    """
    Extract primary color from PPT (V1.0: use default for now).

    In future: Use colorgram.py to extract dominant color from first slide.
    For now: Return a professional default blue.
    """
    # Default professional color scheme
    return "#0056b3"  # Deep blue for government/institutional docs


def render_html(
    slides_data,
    template_path="template.html",
    output_path="output/output.html",
    primary_color=None
):
    """
    Render HTML from translated slides data.

    Args:
        slides_data: List of translated slide dictionaries
        template_path: Path to Jinja2 HTML template
        output_path: Where to save the generated HTML
        primary_color: Hex color code (optional, will use default if None)

    Returns:
        Path to generated HTML file
    """
    # Load template
    template_path = Path(template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    template = Template(template_content)

    # Extract metadata from first slide for cover
    first_slide = slides_data[0] if slides_data else {}

    cover_title = "Document Traduit"
    cover_subtitle = "Traduction et restructuration automatiques avec IA"
    metadata = "Généré avec Layout-Aware AI Engine"

    # Try to extract meaningful title from first slide
    if first_slide:
        original_title = first_slide.get('original_title', '')
        if 'Survey' in original_title or 'Report' in original_title:
            cover_title = first_slide.get('french_title', cover_title)
            cover_subtitle = first_slide.get('summary_one_liner', cover_subtitle)

    # Get primary color
    if not primary_color:
        primary_color = extract_primary_color()

    # Prepare template variables
    template_vars = {
        'document_title': 'Document Traduit - French Translation',
        'cover_title': cover_title,
        'cover_subtitle': cover_subtitle,
        'metadata': metadata,
        'primary_color': primary_color,
        'slides': slides_data
    }

    # Render HTML
    html_content = template.render(**template_vars)

    # Save to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_path


def main():
    """Main entry point."""
    # Load translated slides
    input_path = Path("output/translated_slides.json")
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found. Run translate_ai.py first.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} translated slides")

    # Render HTML
    output_path = render_html(
        slides_data=slides_data,
        template_path="template.html",
        output_path="output/output.html"
    )

    print(f"✅ HTML generated: {output_path}")
    print(f"\n📊 Summary:")
    print(f"  - Total slides: {len(slides_data)}")
    print(f"  - Template: template.html")
    print(f"  - Output: {output_path}")

    print(f"\n🌐 To view:")
    print(f"  Open {output_path.absolute()} in your browser")
    print(f"  Or run: open {output_path}")


if __name__ == "__main__":
    main()
