#!/usr/bin/env python3
"""
Stage 3 V5: HTML Rendering for Restructured Content
Renders AI-restructured slides (may include split slides like 2.1, 2.2).
"""

import json
import sys
import re
from pathlib import Path
from jinja2 import Template


def markdown_to_html(text):
    """
    Convert markdown emphasis to HTML.

    Supports:
    - ***text*** → <strong><em>text</em></strong> (bold + italic)
    - **text** → <strong>text</strong> (bold)
    - *text* → <em>text</em> (italic)
    """
    if not text:
        return text

    # Order matters: process triple first, then double, then single
    # ***text*** → <strong><em>text</em></strong>
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'<strong><em>\1</em></strong>', text)
    # **text** → <strong>text</strong>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # *text* → <em>text</em>
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)

    return text


def process_slide_markdown(slide):
    """Apply markdown conversion to all text fields in a slide."""
    # Process title
    if slide.get('french_title'):
        slide['french_title'] = markdown_to_html(slide['french_title'])

    # Process summary
    if slide.get('summary_one_liner'):
        slide['summary_one_liner'] = markdown_to_html(slide['summary_one_liner'])

    # Process bullet points
    if slide.get('french_points'):
        slide['french_points'] = [markdown_to_html(point) for point in slide['french_points']]

    # Process quote text
    if slide.get('quote_text'):
        slide['quote_text'] = markdown_to_html(slide['quote_text'])

    # Process card labels
    if slide.get('cards'):
        for card in slide['cards']:
            if card.get('label'):
                card['label'] = markdown_to_html(card['label'])
            if card.get('sublabel'):
                card['sublabel'] = markdown_to_html(card['sublabel'])

    # Process table content
    if slide.get('translated_tables'):
        for table in slide['translated_tables']:
            # Headers
            if table.get('headers'):
                table['headers'] = [markdown_to_html(h) for h in table['headers']]
            # Rows
            if table.get('rows'):
                table['rows'] = [
                    [markdown_to_html(cell) for cell in row]
                    for row in table['rows']
                ]

    return slide


def render_html_v5(
    slides_data,
    template_path="template_v4.html",  # Reuse V4 template (supports all layouts)
    output_path="output/output_v5.html",
    primary_color="#0056b3"
):
    """
    Render HTML from V5 restructured slides data.

    Args:
        slides_data: List of flattened slide dictionaries (from V5)
        template_path: Path to Jinja2 HTML template
        output_path: Where to save the generated HTML
        primary_color: Hex color code

    Returns:
        Path to generated HTML file
    """
    template_path = Path(template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    template = Template(template_content)

    # Process markdown in all slides
    slides_data = [process_slide_markdown(slide) for slide in slides_data]

    # Extract metadata from first slide for cover
    first_slide = slides_data[0] if slides_data else {}

    cover_title = first_slide.get('french_title', 'Document Traduit')
    cover_subtitle = first_slide.get('summary_one_liner', 'Présentation professionnelle restructurée par IA')
    metadata = "Généré avec V5 AI Content Restructuring System"

    # Prepare template variables
    template_vars = {
        'document_title': 'Document Traduit - V5 Restructured',
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
    # Load V5 flattened slides
    input_path = Path("output/translated_slides_v5.json")
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found. Run translate_ai_v5.py first.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} output slides (V5 restructured)")

    # Count source slides vs output slides
    source_ids = set()
    for slide in slides_data:
        source_id = slide.get('source_id', slide.get('id'))
        if isinstance(source_id, str) and '.' in source_id:
            source_id = source_id.split('.')[0]
        source_ids.add(source_id)

    print(f"   From {len(source_ids)} source slides")

    # Count layout types
    layout_counts = {}
    for slide in slides_data:
        layout = slide.get('layout_type', 'unknown')
        layout_counts[layout] = layout_counts.get(layout, 0) + 1

    print(f"\n📊 Layout Distribution:")
    for layout, count in sorted(layout_counts.items()):
        icon = {
            "text_bullets": "📝",
            "styled_table": "📋",
            "clean_cards": "🎯",
            "section_header": "📌",
            "bar_chart": "📊",
            "column_chart": "📊",
            "pie_chart": "🥧",
            "line_chart": "📈",
            "chart_image": "🖼️",
            "quote": "💬"
        }.get(layout, "❓")
        print(f"   {icon} {layout}: {count}")

    # Render HTML
    output_path = render_html_v5(
        slides_data=slides_data,
        template_path="template_v4.html",
        output_path="output/output_v5.html"
    )

    print(f"\n✅ HTML generated: {output_path}")
    print(f"\n🌐 To view:")
    print(f"  open {output_path}")


if __name__ == "__main__":
    main()
