#!/usr/bin/env python3
"""
Render V5 Quote Demo - showing Slide 9 as a quote instead of cards
"""

import json
import sys
from pathlib import Path
from jinja2 import Template


def main():
    # Load quote demo version
    input_path = Path("output/translated_slides_v5_quote_demo.json")

    with open(input_path, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    print(f"📖 Loaded {len(slides_data)} slides (V5 Quote Demo)")

    # Load template
    template_path = Path("template_v4.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    template = Template(template_content)

    # Prepare template variables
    first_slide = slides_data[0] if slides_data else {}

    template_vars = {
        'document_title': 'Document Traduit - V5 Quote Demo',
        'cover_title': first_slide.get('french_title', 'Document Traduit'),
        'cover_subtitle': 'Démonstration du layout Quote (Slide 9 convertie)',
        'metadata': 'V5 avec layout Quote - Démonstration',
        'primary_color': '#0056b3',
        'slides': slides_data
    }

    # Render HTML
    html_content = template.render(**template_vars)

    # Save to file
    output_path = Path("output/output_v5_quote_demo.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Count layouts
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
            "quote": "💬"
        }.get(layout, "❓")

        indicator = " ⭐ DEMO" if layout == "quote" else ""
        print(f"   {icon} {layout}: {count}{indicator}")

    print(f"\n✅ Quote demo HTML generated: {output_path}")
    print(f"\n🌐 To view:")
    print(f"  open {output_path}")
    print(f"\n📌 Slide 9 has been converted to QUOTE layout for demonstration")


if __name__ == "__main__":
    main()
