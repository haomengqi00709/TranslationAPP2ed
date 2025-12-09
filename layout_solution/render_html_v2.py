#!/usr/bin/env python3
"""
Stage 3 V2: HTML Rendering with Content-Aware Layouts
Renders different slide types (text, table, section_header) appropriately.
"""

import json
import sys
from pathlib import Path
from jinja2 import Template


def render_html_v2(
    slides_data,
    template_path="template_v2.html",
    output_path="output/output_v2.html",
    primary_color="#0056b3"
):
    """
    Render HTML from translated slides data (V2 format with tables).

    Args:
        slides_data: List of translated slide dictionaries
        template_path: Path to Jinja2 HTML template
        output_path: Where to save the generated HTML
        primary_color: Hex color code

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

    cover_title = first_slide.get('french_title', 'Document Traduit')
    cover_subtitle = first_slide.get('summary_one_liner', 'Traduction et restructuration automatiques avec IA')
    metadata = "Généré avec Layout-Aware AI Engine V2.0"

    # Prepare template variables
    template_vars = {
        'document_title': 'Document Traduit - Traduction Française V2',
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
    # Load translated slides (V2)
    input_path = Path("output/translated_slides_v2.json")
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found. Run translate_ai_v2.py first.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} translated slides (V2 format)")

    # Count slide types
    type_counts = {}
    for slide in slides_data:
        slide_type = slide.get('type', 'unknown')
        type_counts[slide_type] = type_counts.get(slide_type, 0) + 1

    print(f"   📝 Text slides: {type_counts.get('text', 0)}")
    print(f"   📊 Table slides: {type_counts.get('table', 0)}")
    print(f"   📌 Section headers: {type_counts.get('section_header', 0)}")

    # Render HTML
    output_path = render_html_v2(
        slides_data=slides_data,
        template_path="template_v2.html",
        output_path="output/output_v2.html"
    )

    print(f"\n✅ HTML generated: {output_path}")
    print(f"\n🌐 To view:")
    print(f"  open {output_path}")


if __name__ == "__main__":
    main()
